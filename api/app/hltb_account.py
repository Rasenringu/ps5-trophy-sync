"""Browser-session HLTB connector. Provider cookies never enter this server.

Receipts describe the paired browser's read-back; this is not provider OAuth or
an independently server-authenticated HLTB identity. No background publication.
"""
import secrets
from typing import Annotated, Literal
from fastapi import APIRouter,Depends,Request,HTTPException
from pydantic import Field
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from .contracts import Strict
from .db import database
from .models import HltbPairing,HltbConnection,HltbPublication,GameInsight
from .main import browser,bearer,digest,fail,now,rate
from .insights import GameKey,ExternalId,game_rows,game_title,platform
from . import howlongtobeat

router=APIRouter()

class Empty(Strict):pass

class Claim(Strict):
    code: Annotated[str,Field(min_length=32,max_length=64,pattern=r'^[A-Za-z0-9_-]+$')]
    user_id: ExternalId
    username: Annotated[str,Field(pattern=r'^[A-Za-z0-9_]{3,20}$')]

class Publish(GameKey):
    hltb_id: ExternalId
    seconds: Annotated[int,Field(strict=True,ge=1,le=36000000)]
    confirm: Annotated[bool,Field(strict=True)]

class Receipt(Strict):
    job_id: Annotated[str,Field(pattern=r'^[a-f0-9]{64}$')]
    state: Literal['synced','failed','uncertain']
    submission_id: ExternalId | None=None
    seconds: Annotated[int,Field(strict=True,ge=1,le=36000000)] | None=None
    error: Literal['sign_in_required','account_changed','ambiguous_entries','existing_time_greater',
        'invalid_response','provider_unavailable','rate_limited','write_unverified','game_unavailable'] | None=None

def connection(db,owner):
    row=db.get(HltbConnection,owner)
    return row if row and row.token and row.expires>now() else None

def connector(request: Request,db: Session=Depends(database)):
    row=db.scalar(select(HltbConnection).where(HltbConnection.token==bearer(request),HltbConnection.expires>now()).with_for_update())
    if not row:fail(401,'Reconnect the HowLongToBeat browser connector')
    return row

def job_view(row):
    return {k:getattr(row,k) for k in ('id','source','title_id','hltb_id','title','platform','seconds','state','updated','submission_id','error')}

@router.get('/account/integrations/howlongtobeat/connection')
def status(owner: str=Depends(browser),db: Session=Depends(database)):
    row=connection(db,owner)
    jobs=db.scalars(select(HltbPublication).where(HltbPublication.account==owner).order_by(HltbPublication.updated.desc()).limit(30))
    return {'connected':row is not None,'username':row.username if row else None,
            'expires':row.expires if row else None,'last_seen':row.last_seen if row else None,
            'publications':[job_view(job) for job in jobs]}

@router.post('/account/integrations/howlongtobeat/connect')
def begin(body: Empty,owner: str=Depends(browser),db: Session=Depends(database)):
    rate(db,'hltb-connect:'+owner,5,600)
    code=secrets.token_urlsafe(24);expires=now()+600
    db.execute(insert(HltbPairing).values(account=owner,code=digest(code),expires=expires)
        .on_conflict_do_update(index_elements=['account'],set_={'code':digest(code),'expires':expires}))
    db.commit()
    return {'code':code,'expires':expires,'login_url':'https://howlongtobeat.com/login'}

@router.post('/integrations/howlongtobeat/claim')
def claim(body: Claim,request: Request,db: Session=Depends(database)):
    rate(db,'hltb-claim:'+str(request.client.host if request.client else 'unknown'),10,600)
    row=db.scalar(select(HltbPairing).where(HltbPairing.code==digest(body.code)).with_for_update())
    if not row or row.expires<=now():fail(401,'Connection code expired or already used')
    token=secrets.token_urlsafe(32);expires=now()+30*86400
    db.scalar(select(HltbConnection).where(HltbConnection.account==row.account).with_for_update())
    # Relinking never transfers pending jobs to a different provider login.
    for job in db.scalars(select(HltbPublication).where(HltbPublication.account==row.account,HltbPublication.state.in_(['pending','processing','uncertain']))):
        job.state='cancelled';job.updated=now()
    db.execute(insert(HltbConnection).values(account=row.account,token=digest(token),user_id=body.user_id,
        username=body.username,expires=expires,last_seen=now()).on_conflict_do_update(index_elements=['account'],
        set_={'token':digest(token),'user_id':body.user_id,'username':body.username,'expires':expires,'last_seen':now()}))
    db.delete(row);db.commit()
    return {'token':token,'expires':expires,'username':body.username}

@router.post('/account/integrations/howlongtobeat/disconnect')
def disconnect(body: Empty,owner: str=Depends(browser),db: Session=Depends(database)):
    pair=db.scalar(select(HltbPairing).where(HltbPairing.account==owner).with_for_update())
    row=db.scalar(select(HltbConnection).where(HltbConnection.account==owner).with_for_update())
    if row:row.token=None;row.expires=now()
    if pair:db.delete(pair)
    for job in db.scalars(select(HltbPublication).where(HltbPublication.account==owner,HltbPublication.state.in_(['pending','processing','uncertain']))):
        job.state='cancelled';job.updated=now()
    db.commit();return {'connected':False}

@router.post('/account/games/howlongtobeat/publish')
def publish(body: Publish,owner: str=Depends(browser),db: Session=Depends(database)):
    from .social import counted
    rate(db,'hltb-publish:'+owner,12,60)
    if not body.confirm:fail(422,'Review and confirm the progress time first')
    rows=game_rows(db,owner,body.source,body.title_id)
    if any(r.get('game_hidden') for r in rows):fail(422,'Unhide this game before publishing')
    link=connection(db,owner)
    if not link:fail(409,'Connect your HowLongToBeat browser first')
    expected_token=link.token
    seconds=sum(r['data']['duration_seconds'] for r in rows if r['kind']=='activity' and counted(r['data']))
    if seconds!=body.seconds:fail(409,'Recorded playtime changed; review it again')
    title=game_title(rows)
    note=db.get(GameInsight,(owner,body.source,body.title_id))
    resolved=howlongtobeat.resolve(db,title,'PlayStation 4' if platform(body.source,body.title_id)=='PS4' else 'PlayStation 5',
        note.hltb_id if note else None)
    if not resolved['game'] or resolved['game']['hltb_id']!=body.hltb_id or resolved['stale'] or resolved['status']!='ok':
        fail(422,'Choose and verify the matching HowLongToBeat game first')
    link=db.scalar(select(HltbConnection).where(HltbConnection.account==owner).with_for_update().execution_options(populate_existing=True))
    if not link or link.token!=expected_token or link.expires<=now():fail(409,'Connect your HowLongToBeat browser first')
    identity=digest(':'.join([owner,str(link.user_id),body.source,body.title_id,str(body.hltb_id),str(seconds)]))
    db.execute(insert(HltbPublication).values(id=identity,account=owner,user_id=link.user_id,source=body.source,
        title_id=body.title_id,hltb_id=body.hltb_id,title=resolved['game']['title'],
        platform='PlayStation 4' if platform(body.source,body.title_id)=='PS4' else 'PlayStation 5',
        seconds=seconds,state='pending',updated=now()).on_conflict_do_nothing())
    job=db.get(HltbPublication,identity,populate_existing=True)
    if job.state in ('failed','cancelled'):job.state='pending';job.error=None;job.updated=now()
    db.commit();return job_view(job)

@router.post('/integrations/howlongtobeat/next')
def next_job(body: Empty,link: HltbConnection=Depends(connector),db: Session=Depends(database)):
    expected_token=link.token
    rate(db,'hltb-next:'+link.account,30,60)
    # Reacquire the connection lock after rate() commits, serialize browser runs.
    link=db.scalar(select(HltbConnection).where(HltbConnection.account==link.account).with_for_update().execution_options(populate_existing=True))
    if not link.token or link.token!=expected_token or link.expires<=now():fail(401,'Reconnect the HowLongToBeat browser connector')
    link.last_seen=now()
    jobs=db.scalars(select(HltbPublication).where(HltbPublication.account==link.account,HltbPublication.user_id==link.user_id,
        HltbPublication.state.in_(['pending','processing','uncertain'])).order_by(HltbPublication.updated).with_for_update()).all()
    for job in jobs:
        # A second browser run cannot post again while the first owns its lease.
        if job.state=='processing' and job.updated>now()-120:continue
        try:rows=game_rows(db,link.account,job.source,job.title_id)
        except HTTPException as error:
            if error.status_code!=404:raise
            job.state='cancelled';job.updated=now();continue
        if any(r.get('game_hidden') for r in rows):job.state='cancelled';job.updated=now();continue
        reconcile=job.attempted
        job.attempted=True;job.state='processing';job.updated=now();db.commit()
        return {'job':job_view(job),'user_id':link.user_id,'reconcile_only':reconcile}
    db.commit();return {'job':None,'user_id':link.user_id}

@router.post('/integrations/howlongtobeat/receipt')
def receipt(body: Receipt,link: HltbConnection=Depends(connector),db: Session=Depends(database)):
    expected_token=link.token
    rate(db,'hltb-receipt:'+link.account,30,60)
    link=db.scalar(select(HltbConnection).where(HltbConnection.account==link.account).with_for_update().execution_options(populate_existing=True))
    if not link.token or link.token!=expected_token or link.expires<=now():fail(401,'Reconnect the HowLongToBeat browser connector')
    job=db.scalar(select(HltbPublication).where(HltbPublication.id==body.job_id,HltbPublication.account==link.account,
        HltbPublication.user_id==link.user_id).with_for_update())
    if not job:fail(404,'Publication not found')
    if job.state=='synced':return job_view(job)
    if job.state!='processing':fail(409,'Publication is no longer active')
    if body.state=='synced' and (not body.submission_id or body.seconds!=job.seconds or body.error):
        fail(422,'A matching read-back is required')
    if body.state!='synced' and not body.error:fail(422,'An action-specific error is required')
    job.state=body.state;job.error=body.error;job.submission_id=body.submission_id;job.updated=now()
    if body.state=='failed':job.attempted=False
    db.commit();return job_view(job)
