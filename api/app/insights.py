"""Account-owned external information; console state is never changed here."""
import csv
import io
from typing import Annotated, Literal
from urllib.parse import urlencode
from fastapi import APIRouter, Depends, Query, Request, Response
from pydantic import Field
from sqlalchemy.orm import Session
from sqlalchemy import select
from .contracts import Strict
from .db import database
from .models import GameInsight, DevicePackage, TrophyText
from .main import browser, fail, library, now, rate
from . import platprices, howlongtobeat

router=APIRouter()
Source=Literal['ps5_native','ps4_bc']
Title=Annotated[str,Field(min_length=1,max_length=64,pattern=r'^[A-Za-z0-9_:-]+$')]
Seconds=Annotated[int,Field(strict=True,ge=1,le=36000000)]
ExternalId=Annotated[int,Field(strict=True,ge=1,le=2147483647)]

class GameKey(Strict):
    source: Source
    title_id: Title

class CompletionEdit(GameKey):
    hltb_id: ExternalId | None=None
    main_seconds: Seconds | None=None
    extra_seconds: Seconds | None=None
    completionist_seconds: Seconds | None=None

class ListingEdit(GameKey):
    platprices_id: ExternalId | None

class AutomaticCompletion(GameKey):
    hltb_id: ExternalId | None=None

def game_rows(db,owner,source,title_id,shared=False):
    rows=[r for r in library(owner,db,'en-US') if not r['mock'] and r['source']==source
          and r['data']['title_id']==title_id and (not shared or not r.get('game_hidden'))]
    if not rows:fail(404,'Game not found in this library')
    # A collection launcher cannot establish completion times for its components.
    if any(r['data'].get('collection_title_id')==title_id for r in rows):
        fail(422,'Choose an individual game in this collection')
    return rows

def publisher_roster(db,rows):
    """Use private publisher definitions internally, including secret names.

    Only numerical rates leave this module. library() has already enforced
    active profile/source ownership; definitions cannot grant game access.
    """
    from .locales import choose_language
    result=[]
    for row in rows:
        data=dict(row['data']);row={**row,'data':data}
        if row['kind']=='trophy':
            package=db.get(DevicePackage,(row['profile_uuid'],data['title_id']))
            if package and (package.metadata_json.get('format')=='ps4_trp_v3')==(row['source']=='ps4_bc'):
                bundle=package.metadata_json
                language=choose_language(list(bundle['texts']),'en-US',bundle['default'])
                text=bundle['texts'][language].get(data['trophy_id'])
                if text:data['name']=text[0]
            else:
                texts=list(db.scalars(select(TrophyText).where(TrophyText.source==row['source'],
                    TrophyText.title_id==data['title_id'],TrophyText.trophy_id==data['trophy_id'])))
                if texts:
                    language=choose_language([t.language for t in texts],'en-US',
                        next((t.language for t in texts if t.is_default),texts[0].language))
                    data['name']=next(t.name for t in texts if t.language==language)
        result.append(row)
    return result

def owned_note(db,owner,source,title_id):
    note=db.get(GameInsight,(owner,source,title_id))
    if not note:
        note=GameInsight(account=owner,source=source,title_id=title_id,updated=now())
        db.add(note)
    return note

def platform(source,title_id):
    return 'PS4' if source=='ps4_bc' or title_id.startswith('CUSA') else 'PS5'

def provider_listing(db,ppid,rows,fetch=True):
    listing=platprices.cached(db,'/games/'+str(ppid),{},fetch)
    summary={k:listing[k] for k in ('status','stale','fetched')}
    summary.update(listing=None,rates={})
    if not listing['data']:return summary
    game=listing['data']
    if game['id']!=ppid or game['platform']!=platform(rows[0]['source'],rows[0]['data']['title_id']):
        return {**summary,'status':'mismatch'}
    trophy_data=platprices.cached(db,'/games/'+str(ppid)+'/trophies',{},fetch)
    summary.update(status=trophy_data['status'],stale=listing['stale'] or trophy_data['stale'],
                   fetched=min(listing['fetched'] or now(),trophy_data['fetched'] or now()),listing=game)
    if not trophy_data['data']:return summary
    if trophy_data['data']['ppid']!=ppid:return {**summary,'status':'mismatch'}
    rates=platprices.match_rates(trophy_data['data'],publisher_roster(db,rows))
    if rates is None:return {**summary,'status':'mismatch'}
    return {**summary,'rates':rates}

def describe(db,owner,source,title_id,rows,fetch=True):
    note=db.get(GameInsight,(owner,source,title_id))
    title=next((r['data']['title'] for r in rows if r['kind']=='trophy'),rows[0]['data']['title'])
    completion={k:getattr(note,k,None) for k in ('hltb_id','main_seconds','extra_seconds','completionist_seconds')}
    completion.update(url='https://howlongtobeat.com/game/'+str(note.hltb_id) if note and note.hltb_id else
        'https://howlongtobeat.com/?'+urlencode({'q':title}),
        entry_mode='manual',updated=note.updated if note else None,status='manual',stale=False,candidates=[])
    if not note or note.hltb_mode!='manual':
        result=howlongtobeat.resolve(db,title,'PlayStation 4' if platform(source,title_id)=='PS4' else 'PlayStation 5',
            note.hltb_id if note else None,fetch)
        completion.update({k:None for k in ('main_seconds','extra_seconds','completionist_seconds')})
        completion.update(entry_mode='provider',status=result['status'],stale=result['stale'],
                          updated=result['fetched'],candidates=result['candidates'] if fetch and not result['game'] else [])
        if result['game']:completion.update(result['game'])
    rarity={'status':'not_selected' if platprices.configured() else 'not_configured',
            'listing':None,'rates':{},'fetched':None,'stale':False}
    if note and note.platprices_id:
        rarity=provider_listing(db,note.platprices_id,rows,fetch)
    return {'howlongtobeat':completion,'rarity':rarity}

@router.get('/account/integrations')
def integrations(owner: str=Depends(browser)):
    return {'howlongtobeat':{'automatic_fetch':howlongtobeat.enabled(),'account_sync':False,'entry_mode':'provider'},
            'platprices':{'configured':platprices.configured(),'region':platprices.settings()[1] if platprices.configured() else None}}

@router.get('/account/games/insights')
def insights(source: Source,title_id: Title,owner: str=Depends(browser),db: Session=Depends(database)):
    rate(db,'insights:'+owner,60,60)
    rows=game_rows(db,owner,source,title_id)
    return describe(db,owner,source,title_id,rows)

@router.post('/account/games/howlongtobeat')
def completion(body: CompletionEdit,owner: str=Depends(browser),db: Session=Depends(database)):
    rate(db,'insights-edit:'+owner,60,60)
    rows=game_rows(db,owner,body.source,body.title_id)
    note=owned_note(db,owner,body.source,body.title_id)
    for field in ('hltb_id','main_seconds','extra_seconds','completionist_seconds'):
        setattr(note,field,getattr(body,field))
    note.hltb_mode='manual';note.updated=now();db.commit()
    return describe(db,owner,body.source,body.title_id,rows,False)

@router.post('/account/games/howlongtobeat/automatic')
def automatic_completion(body: AutomaticCompletion,owner: str=Depends(browser),db: Session=Depends(database)):
    rate(db,'hltb-select:'+owner,12,60)
    rows=game_rows(db,owner,body.source,body.title_id)
    if body.hltb_id:
        title=rows[0]['data']['title']
        result=howlongtobeat.resolve(db,title,'PlayStation 4' if platform(body.source,body.title_id)=='PS4' else 'PlayStation 5',body.hltb_id)
        if not result['game'] or result['status']!='ok' or result['stale']:
            fail(422,'The HowLongToBeat listing could not be verified for this platform')
    note=owned_note(db,owner,body.source,body.title_id)
    note.hltb_mode='automatic';note.hltb_id=body.hltb_id
    note.main_seconds=note.extra_seconds=note.completionist_seconds=None
    db.commit()
    return describe(db,owner,body.source,body.title_id,rows)

@router.get('/account/integrations/howlongtobeat/search')
def search_completion(source: Source,title_id: Title,owner: str=Depends(browser),db: Session=Depends(database)):
    rate(db,'hltb-search:'+owner,12,60)
    rows=game_rows(db,owner,source,title_id)
    title=next((r['data']['title'] for r in rows if r['kind']=='trophy'),rows[0]['data']['title'])
    result=howlongtobeat.resolve(db,title,'PlayStation 4' if platform(source,title_id)=='PS4' else 'PlayStation 5')
    return {k:result[k] for k in ('status','candidates','stale','fetched')}

@router.get('/account/integrations/platprices/search')
def search(source: Source,title_id: Title,owner: str=Depends(browser),db: Session=Depends(database)):
    rate(db,'provider-search:'+owner,12,60)
    rows=game_rows(db,owner,source,title_id)
    title=next((r['data']['title'] for r in rows if r['kind']=='trophy'),rows[0]['data']['title'])
    response=platprices.cached(db,'/games/search',{'q':title[:200],'limit':25,'platform':platform(source,title_id).lower()})
    return {k:response[k] for k in ('status','stale','fetched')} | {
        'games':[g for g in (response['data'] or {}).get('games',[]) if g['platform']==platform(source,title_id)]}

@router.post('/account/games/platprices')
def select_listing(body: ListingEdit,owner: str=Depends(browser),db: Session=Depends(database)):
    rate(db,'provider-select:'+owner,12,60)
    rows=game_rows(db,owner,body.source,body.title_id)
    if body.platprices_id is not None:
        check=provider_listing(db,body.platprices_id,rows)
        if check['status']!='ok' or not check['rates'] or check['stale']:
            fail(422,'The listing could not be verified against this game trophy list')
    note=owned_note(db,owner,body.source,body.title_id)
    note.platprices_id=body.platprices_id;db.commit()
    return describe(db,owner,body.source,body.title_id,rows,False)

@router.get('/players/{handle}/games/insights')
def shared_insights(handle: str,source: Source,title_id: Title,request: Request,db: Session=Depends(database)):
    from .social import optional_viewer, shared_access
    peer=shared_access(db,handle,optional_viewer(request,db))
    rows=game_rows(db,peer.account,source,title_id,True)
    # Public viewers can only read the owner's existing cache. They cannot
    # initiate third-party requests or consume the host's monthly quota.
    return describe(db,peer.account,source,title_id,rows,False)

def csv_cell(value):
    text=str(value)
    return "'"+text if text.lstrip().startswith(('=','+','-','@')) or text.startswith(('\t','\r','\n')) else text

@router.get('/account/integrations/playtime.csv')
def export_playtime(owner: str=Depends(browser),db: Session=Depends(database)):
    from .social import counted
    rate(db,'playtime-export:'+owner,6,60)
    games={}
    for row in library(owner,db,'en-US'):
        if row['mock'] or row.get('game_hidden'):continue
        data=row['data'];key=(row['source'],data.get('collection_title_id') or data['title_id'])
        game=games.setdefault(key,{'title':data.get('collection_title') or data['title'],'seconds':None,'trophies':{}})
        if row['kind']=='activity' and counted(data):game['seconds']=(game['seconds'] or 0)+data['duration_seconds']
        if row['kind']=='trophy':
            trophy=(data['title_id'],data['trophy_id'])
            game['trophies'][trophy]=game['trophies'].get(trophy,False) or data.get('unlocked') is True
    output=io.StringIO(newline='');writer=csv.writer(output)
    writer.writerow(['Game','Platform','Recorded hours (not completion time)','Earned trophies','Imported trophies'])
    for (source,title),game in sorted(games.items(),key=lambda item:item[1]['title'].casefold()):
        writer.writerow([csv_cell(game['title']),platform(source,title),
            '' if game['seconds'] is None else round(game['seconds']/3600,3),sum(game['trophies'].values()),len(game['trophies'])])
    return Response('\ufeff'+output.getvalue(),media_type='text/csv; charset=utf-8',
                    headers={'Content-Disposition':'attachment; filename="trophysync-playtime.csv"'})
