"""Public identities, explicit friendships, viewer-safe trophy comparisons."""
import re
import uuid
from typing import Literal
from fastapi import APIRouter, Depends, Request, Response, Query
from pydantic import Field, field_validator
from sqlalchemy import select, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .db import database
from .contracts import Strict
from .models import Account, Login, Profile, Record, Artwork, DeviceArtwork, SocialProfile, Friendship
from .main import browser, digest, now, rate, fail, library

router=APIRouter()
Handle=str

class ProfileEdit(Strict):
    handle: str=Field(pattern=r'^[a-z][a-z0-9_]{2,31}$')
    display_name: str=Field(min_length=1,max_length=60)
    visibility: Literal['public','friends']|None=None
    @field_validator('display_name')
    @classmethod
    def clean(cls,value):
        value=value.strip()
        if not value or any(ord(c)<32 or 127<=ord(c)<160 for c in value):raise ValueError('Invalid display name')
        return value

class FriendRequest(Strict):
    handle: str=Field(pattern=r'^[a-z][a-z0-9_]{2,31}$')

class FriendAction(Strict):
    action: Literal['accept','deny','cancel','remove']

def ensure_social(db,account):
    profile=db.scalar(select(SocialProfile).where(SocialProfile.account==account))
    if not profile:
        suffix=uuid.uuid4().hex[:12]
        profile=SocialProfile(handle='player_'+suffix,account=account,display_name='Player '+suffix[:6])
        db.add(profile);db.flush()
    return profile

def identity(profile):return {'handle':profile.handle,'display_name':profile.display_name}

def target(db,handle):
    if not re.fullmatch(r'[a-z][a-z0-9_]{2,31}',handle):fail(404,'Player not found')
    profile=db.get(SocialProfile,handle)
    if not profile:fail(404,'Player not found')
    return profile

def optional_viewer(request,db):
    login=db.get(Login,digest(request.cookies.get('session','')))
    return login.account if login and login.expires>now() else None

def edge(db,a,b):
    first,second=sorted((a,b))
    return db.scalar(select(Friendship).where(Friendship.first==first,Friendship.second==second))

def relationship(link,viewer,peer):
    if viewer==peer:return 'self'
    if not link or link.state=='denied':return 'none'
    if link.state=='accepted':return 'friends'
    return 'outgoing' if link.requester==viewer else 'incoming'

def require_friend(db,owner,handle):
    peer=target(db,handle);link=edge(db,owner,peer.account)
    if not link or link.state!='accepted':fail(403,'Accept a friend request before comparing libraries')
    return peer

@router.get('/account/profile')
def own_profile(owner: str=Depends(browser),db: Session=Depends(database)):
    profile=ensure_social(db,owner)
    result={**identity(profile),'visibility':profile.visibility};db.commit();return result

@router.post('/account/profile')
def edit_profile(body: ProfileEdit,owner: str=Depends(browser),db: Session=Depends(database)):
    rate(db,'social-edit:'+owner,20,600)
    # Lock the account to serialize edits/first identity creation.
    db.scalar(select(Account).where(Account.id==owner).with_for_update())
    profile=ensure_social(db,owner);profile.handle,profile.display_name=body.handle,body.display_name
    if body.visibility is not None:profile.visibility=body.visibility
    try:db.commit()
    except IntegrityError:db.rollback();fail(409,'That profile handle is already taken')
    return {**identity(profile),'visibility':profile.visibility}

@router.get('/players')
def search_players(q: str,request: Request,db: Session=Depends(database)):
    if not 2<=len(q.strip())<=50:fail(422,'Enter at least two characters to find a player')
    rate(db,'player-search:'+request.client.host,60,60)
    term=q.strip()
    profiles=db.scalars(select(SocialProfile).where(or_(SocialProfile.handle.icontains(term,autoescape=True),SocialProfile.display_name.icontains(term,autoescape=True))).order_by(SocialProfile.handle).limit(20))
    return [identity(p) for p in profiles]

@router.get('/players/{handle}')
def public_profile(handle: str,request: Request,db: Session=Depends(database)):
    peer=target(db,handle);viewer=optional_viewer(request,db)
    link=edge(db,viewer,peer.account) if viewer else None
    status=relationship(link,viewer,peer.account)
    return {**identity(peer),'relationship':status,'viewer_authenticated':viewer is not None,
        'request_id':link.id if link and status in ('incoming','outgoing','friends') else None,
        'library_visible':peer.visibility=='public' or status in ('self','friends')}

def shared_access(db,handle,viewer):
    peer=target(db,handle)
    if peer.visibility!='public' and viewer!=peer.account:
        link=edge(db,viewer,peer.account) if viewer else None
        if not link or link.state!='accepted':fail(403,'This library is shared with friends only')
    return peer

def counted(data):
    return data.get('complete') and data.get('duration_seconds') is not None and (
        data.get('clock')=='trusted' or (data.get('duration_basis')=='native_foreground_seconds'
        and data.get('consistency')=='sqlite_read_transaction'
        and data.get('profile_binding')=='activity_header_single_local_user'))

@router.get('/players/{handle}/library')
def shared_library(handle: str,request: Request,language: str='en',db: Session=Depends(database)):
    viewer=optional_viewer(request,db);peer=shared_access(db,handle,viewer)
    rows=library(peer.account,db,language);trophies=aggregated(rows)
    mine=aggregated(library(viewer,db,language)) if viewer else {}
    result=[];games={}
    fields=('title_id','title','trophy_id','name','description','hidden','grade','unlocked','unlocked_at')
    for key,row in trophies.items():
        data={k:row['data'].get(k) for k in fields}
        viewer_earned=viewer==peer.account or (key in mine and mine[key]['data'].get('unlocked') is True)
        masked=data.get('hidden') is not False and not viewer_earned
        data['concealed']=masked
        if masked:data.update(name='Hidden trophy',description=None,hidden=True)
        elif data.get('hidden') and key in mine:
            data.update(name=mine[key]['data'].get('name'),description=mine[key]['data'].get('description'))
        def image_url(url):return '/api/players/'+peer.handle+'/artwork/'+url.rsplit('/',1)[1] if url else None
        # No profile IDs, native flags or source database details leave this route.
        entry={'profile_uuid':'shared','profile_label':peer.display_name,'source':row['source'],
            'kind':'trophy','mock':False,'data':data,'artwork_url':image_url(row.get('artwork_url')),
            'icon_url':None if masked else image_url(row.get('icon_url'))}
        result.append(entry);games[(key[0],key[1])]=entry
    totals={}
    for row in rows:
        if row['mock'] or row['kind']!='activity' or not counted(row['data']):continue
        key=(row['source'],row['data']['title_id'])
        total=totals.setdefault(key,{'seconds':0,'sessions':0})
        total['seconds']+=row['data']['duration_seconds'];total['sessions']+=1
    for key,total in totals.items():
        if key not in games:continue
        game=games[key]
        result.append({**game,'kind':'activity','icon_url':None,'data':{
            'title_id':key[1],'title':game['data']['title'],'duration_seconds':total['seconds'],
            'complete':True,'duration_basis':'shared_total','session_count':total['sessions']}})
    return result

@router.get('/players/{handle}/artwork/{image_id}')
def shared_image(handle: str,image_id: str,request: Request,db: Session=Depends(database)):
    viewer=optional_viewer(request,db);peer=shared_access(db,handle,viewer)
    image=db.get(DeviceArtwork,image_id) or db.get(Artwork,image_id)
    if not image:fail(404,'Artwork unavailable')
    source='ps5_native' if isinstance(image,DeviceArtwork) else image.source
    records=select(Record).join(Profile,Profile.id==Record.profile).where(
        Profile.owner==peer.account,Profile.revoked==False,Record.mock==False,
        Record.source==source,Record.kind=='trophy',Record.data['title_id'].as_string()==image.title_id)
    if isinstance(image,DeviceArtwork):records=records.where(Record.profile==image.profile)
    if image.trophy_id:records=records.where(Record.data['trophy_id'].as_string()==image.trophy_id,Record.data['unlocked'].as_boolean()==True)
    if db.scalar(records.limit(1)) is None:fail(404,'Artwork unavailable')
    if image.trophy_id:
        peer_rows=aggregated(library(peer.account,db,'en'))
        key=(source,image.title_id,image.trophy_id);row=peer_rows.get(key)
        if not row:fail(404,'Artwork unavailable')
        if row['data'].get('hidden') is not False and viewer!=peer.account:
            mine=aggregated(library(viewer,db,'en')) if viewer else {}
            if key not in mine or mine[key]['data'].get('unlocked') is not True:fail(404,'Artwork unavailable')
    headers={'Cache-Control':'private, no-cache','Vary':'Cookie','ETag':'"'+image.digest+'"'}
    if request.headers.get('if-none-match')==headers['ETag']:return Response(status_code=304,headers=headers)
    return Response(image.content,media_type='image/png',headers=headers)

@router.get('/account/friends')
def friends(owner: str=Depends(browser),db: Session=Depends(database)):
    links=list(db.scalars(select(Friendship).where(or_(Friendship.first==owner,Friendship.second==owner),Friendship.state.in_(['pending','accepted','denied'])).order_by(Friendship.updated.desc(),Friendship.id)))
    peers={p.account:p for p in db.scalars(select(SocialProfile).where(SocialProfile.account.in_({l.second if l.first==owner else l.first for l in links})))} if links else {}
    result={'friends':[],'incoming':[],'outgoing':[],'denied':[]}
    for link in links:
        peer=peers.get(link.second if link.first==owner else link.first)
        if not peer:continue
        if link.state=='denied':
            if link.requester!=owner:continue
            state='denied'
        else:state=relationship(link,owner,peer.account)
        result[state].append({**identity(peer),'request_id':link.id})
    return result

@router.post('/account/friends/request')
def request_friend(body: FriendRequest,owner: str=Depends(browser),db: Session=Depends(database)):
    rate(db,'friend-request:'+owner,20,600)
    peer=target(db,body.handle)
    if owner==peer.account:fail(400,'You cannot send yourself a friend request')
    first,second=sorted((owner,peer.account))
    list(db.scalars(select(Account).where(Account.id.in_([first,second])).order_by(Account.id).with_for_update()))
    link=edge(db,first,second)
    if link and link.state=='denied' and link.updated+86400>now():fail(429,'Please wait before sending another request')
    if not link:
        link=Friendship(id=str(uuid.uuid4()),first=first,second=second,requester=owner,state='pending',updated=now());db.add(link)
    elif link.state=='denied':link.requester,link.state,link.updated=owner,'pending',now()
    db.commit()
    return {'request_id':link.id,'relationship':relationship(link,owner,peer.account)}

@router.post('/account/friends/{request_id}')
def act_friend(request_id: str,body: FriendAction,owner: str=Depends(browser),db: Session=Depends(database)):
    rate(db,'friend-action:'+owner,40,600)
    link=db.scalar(select(Friendship).where(Friendship.id==request_id,or_(Friendship.first==owner,Friendship.second==owner)).with_for_update())
    if not link:fail(404,'Friend request not found')
    if body.action in ('accept','deny'):
        if link.requester==owner:fail(403,'Only the recipient can respond to this request')
        if link.state!='pending':fail(409,'This request is no longer pending')
        link.state='accepted' if body.action=='accept' else 'denied';link.updated=now()
    else:
        if body.action=='cancel' and (link.state!='pending' or link.requester!=owner):fail(403,'Only the sender can cancel a pending request')
        if body.action=='remove' and link.state!='accepted':fail(409,'This friendship is not active')
        db.delete(link)
    db.commit();return {'status':'updated'}

def aggregated(rows):
    result={}
    for row in rows:
        if row['mock'] or row['kind']!='trophy':continue
        d=row['data'];key=(row['source'],d['title_id'],d['trophy_id'])
        old=result.get(key)
        if old is None or d.get('unlocked') is True or (old['data'].get('unlocked') is False and d.get('unlocked') is None):result[key]=row
    return result

@router.get('/account/friends/{handle}/compare')
def compare(handle: str,language: str='en',title_id: str|None=Query(default=None,max_length=64),source: Literal['ps5_native','ps4_bc']|None=None,
            owner: str=Depends(browser),db: Session=Depends(database)):
    peer=require_friend(db,owner,handle)
    mine=aggregated(library(owner,db,language));theirs=aggregated(library(peer.account,db,language))
    groups={}
    for key in sorted(mine.keys()|theirs.keys()):
        platform,title,trophy=key
        if title_id and title!=title_id or source and platform!=source:continue
        a,b=mine.get(key),theirs.get(key);row=a or b;data=row['data']
        game=groups.setdefault((platform,title),{'source':platform,'title_id':title,'title':data['title'],
            'artwork_url':None,'total':0,'mine_earned':0,'friend_earned':0,'trophies':[]})
        if not game['artwork_url'] and row.get('artwork_url'):
            game['artwork_url']=row['artwork_url'] if a else '/api/account/friends/'+peer.handle+'/artwork/'+row['artwork_url'].rsplit('/',1)[1]
        own=a['data'].get('unlocked') if a else None;other=b['data'].get('unlocked') if b else None
        game['total']+=1;game['mine_earned']+=own is True;game['friend_earned']+=other is True
        if title_id:
            # Unknown secret metadata stays concealed until this viewer earns it.
            hidden=any(r and r['data'].get('hidden',True) for r in (a,b))
            masked=hidden and own is not True
            image=a.get('icon_url') if a and own is True else None
            if not image and b and own is True and b.get('icon_url'):image='/api/account/friends/'+peer.handle+'/artwork/'+b['icon_url'].rsplit('/',1)[1]
            game['trophies'].append({'trophy_id':trophy,'grade':data.get('grade'),'hidden':masked,
                'name':'Hidden trophy' if masked else data.get('name'),
                'description':None if masked else data.get('description'),'icon_url':image,
                'mine':own,'friend':other,'mine_present':a is not None,'friend_present':b is not None})
    return {'friend':identity(peer),'games':sorted(groups.values(),key=lambda g:g['title'].casefold())}

@router.get('/account/friends/{handle}/artwork/{image_id}')
def friend_image(handle: str,image_id: str,request: Request,owner: str=Depends(browser),db: Session=Depends(database)):
    peer=require_friend(db,owner,handle)
    image=db.get(DeviceArtwork,image_id) or db.get(Artwork,image_id)
    if not image:fail(404,'Artwork unavailable')
    owned=select(Record.id).join(Profile,Profile.id==Record.profile).where(Profile.owner==peer.account,Profile.revoked==False,
        Record.mock==False,Record.kind=='trophy',Record.source=='ps5_native',Record.data['title_id'].as_string()==image.title_id)
    if isinstance(image,DeviceArtwork):owned=owned.where(Record.profile==image.profile)
    if image.trophy_id:owned=owned.where(Record.data['trophy_id'].as_string()==image.trophy_id)
    if db.scalar(owned.limit(1)) is None:fail(404,'Artwork unavailable')
    if image.trophy_id:
        earned=select(Record.id).join(Profile,Profile.id==Record.profile).where(Profile.owner==owner,Profile.revoked==False,
            Record.mock==False,Record.kind=='trophy',Record.source=='ps5_native',
            Record.data['title_id'].as_string()==image.title_id,Record.data['trophy_id'].as_string()==image.trophy_id,Record.data['unlocked'].as_boolean()==True)
        if db.scalar(earned.limit(1)) is None:fail(404,'Artwork unavailable')
    headers={'Cache-Control':'private, no-cache','Vary':'Cookie','ETag':'"'+image.digest+'"'}
    if request.headers.get('if-none-match')==headers['ETag']:return Response(status_code=304,headers=headers)
    return Response(image.content,media_type='image/png',headers=headers)
