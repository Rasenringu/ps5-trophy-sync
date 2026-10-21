"""Bounded HLTB lookups, authorized by the user for this installation.

Independent protocol adapter informed by the pinned Playnite integration.
Anonymous search-init tokens stay in memory; no account cookies or credentials.
"""
import json
import os
import re
import time
import unicodedata
import httpx
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from .models import ProviderCache
from .platprices import ProviderError, cache_key, integer, retry_seconds

BASE='https://howlongtobeat.com'
MAX_BODY=2*1024*1024

def enabled():
    return os.environ.get('HLTB_ENABLED','true').lower()=='true'

def normalized_title(title):
    return ''.join(c for c in unicodedata.normalize('NFKC',title).casefold() if c.isalnum() or c in '+&#')

def search_title(title):
    # HLTB treats punctuation attached to a word as a literal search term.
    # Keep identity-bearing symbols; turn title separators into word boundaries.
    title=unicodedata.normalize('NFKC',title)
    return ' '.join(''.join(c if c.isalnum() or c in '+&#' else ' ' for c in title).split())[:200]

def human_title(title):
    return isinstance(title,str) and bool(title.strip()) and not re.fullmatch(
        r'(?:NPWR\d{5}_\d{2}|[PC][PCSU]SA\d{5}|[A-Z]{4}\d{5}(?:_\d{2})?)',title.strip(),re.I)

def read_response(client,method,path,**kwargs):
    if path not in ('/api/search/site/init','/api/search/site') and not re.fullmatch(r'/game/[1-9][0-9]{0,9}',path):
        raise ProviderError('invalid_response')
    deadline=time.monotonic()+10
    with client.stream(method,BASE+path,**kwargs) as response:
        if response.status_code==429:raise ProviderError('rate_limited',retry_seconds(response.headers.get('retry-after')))
        if response.status_code in (401,403):raise ProviderError('blocked')
        if response.status_code==404:raise ProviderError('not_found')
        if response.status_code!=200:raise ProviderError()
        if response.headers.get('content-encoding','identity').lower()!='identity':raise ProviderError('invalid_response')
        media=response.headers.get('content-type','').split(';')[0].strip().lower()
        if media!=('text/html' if path.startswith('/game/') else 'application/json'):raise ProviderError('invalid_response')
        chunks=[];size=0
        for chunk in response.iter_bytes():
            size+=len(chunk)
            if size>MAX_BODY or time.monotonic()>deadline:raise ProviderError('invalid_response')
            chunks.append(chunk)
        return b''.join(chunks)

def parse_game(value):
    if not isinstance(value,dict):raise ProviderError('invalid_response')
    identity=integer(value.get('game_id'),1)
    title=value.get('game_name');platforms=value.get('profile_platform','')
    if not isinstance(title,str) or not 1<=len(title)<=400 or not isinstance(platforms,str) or len(platforms)>2000:
        raise ProviderError('invalid_response')
    times={}
    for source,target in [('comp_main','main_seconds'),('comp_plus','extra_seconds'),('comp_100','completionist_seconds')]:
        seconds=value.get(source)
        times[target]=None if seconds is None else integer(seconds,0,36000000) or None
    return {'hltb_id':identity,'title':title,'platforms':[p.strip() for p in platforms.split(',') if p.strip()],
            'url':BASE+'/game/'+str(identity),**times}

def parse_detail(raw,identity):
    # JSON data only, never execute publisher JavaScript or infer DOM ordinals.
    match=re.search(rb'<script\b(?=[^>]*\bid=["\x27]__NEXT_DATA__["\x27])[^>]*>(.*?)</script\s*>',raw,re.S|re.I)
    if not match:raise ProviderError('invalid_response')
    try:
        values=json.loads(match[1])['props']['pageProps']['game']['data']['game']
        if not isinstance(values,list) or len(values)!=1:raise ProviderError('invalid_response')
        result=parse_game(values[0])
        if result['hltb_id']!=identity:raise ProviderError('invalid_response')
        return result
    except (KeyError,IndexError,TypeError,ValueError,RecursionError):
        raise ProviderError('invalid_response') from None

def fetch(kind,query,platform):
    try:
        with httpx.Client(timeout=httpx.Timeout(5,connect=3),follow_redirects=False,trust_env=False,
            headers={'User-Agent':'TrophySync/0.1','Accept-Encoding':'identity','Referer':BASE+'/', 'Origin':BASE}) as client:
            if kind=='detail':return parse_detail(read_response(client,'GET','/game/'+str(query)),int(query))
            auth=json.loads(read_response(client,'GET','/api/search/site/init',params={'t':int(time.time()*1000)}))
            token=auth.get('token') if isinstance(auth,dict) else None
            if not isinstance(token,str) or not 1<=len(token)<=4096 or not token.isascii() or any(ord(c)<33 for c in token):
                raise ProviderError('invalid_response')
            payload={'searchType':'games','searchTerms':query.split(),'searchPage':1,'size':20,
                'searchOptions':{'games':{'userId':0,'platform':platform,'sortCategory':'popular',
                'rangeCategory':'main','rangeTime':{'min':0,'max':0},'rangeYear':{'min':'','max':''},
                'gameplay':{'perspective':'','flow':'','genre':'','difficulty':''},'modifier':''},
                'users':{'sortCategory':'postcount'},'filter':'','sort':0,'randomizer':0},'useCache':True}
            data=json.loads(read_response(client,'POST','/api/search/site',json=payload,headers={'x-auth-token':token}))
            values=data.get('data') if isinstance(data,dict) else None
            if not isinstance(values,list) or len(values)>20:raise ProviderError('invalid_response')
            games=[parse_game(v) for v in values]
            if len({g['hltb_id'] for g in games})!=len(games):raise ProviderError('invalid_response')
            return {'games':games}
    except (httpx.HTTPError,ValueError,TypeError,RecursionError):raise ProviderError() from None

def cached(db,kind,query,platform,refresh=True):
    from .main import now,rate
    empty={'data':None,'fetched':None,'stale':False}
    if not enabled():return {**empty,'status':'disabled'}
    identity=cache_key('hltb-v2',kind,str(query),platform);pause_id=cache_key('hltb-v1','pause')
    def value(row):
        return {'data':row.data if row else None,'fetched':row.fetched if row else None,
                'status':row.status if row else 'not_cached',
                'stale':bool(row and row.data is not None and (row.status!='ok' or row.expires<=now()))}
    if not refresh:return value(db.get(ProviderCache,identity))
    db.execute(insert(ProviderCache).values(key=identity,status='unavailable',expires=0).on_conflict_do_nothing())
    row=db.scalar(select(ProviderCache).where(ProviderCache.key==identity).with_for_update().execution_options(populate_existing=True))
    if row.expires>now():result=value(row);db.commit();return result
    db.commit()
    try:rate(db,'hltb-upstream',30,60)
    except HTTPException as error:
        if error.status_code!=429:raise
        return {**value(row),'status':'rate_limited','stale':row.data is not None}
    row=db.scalar(select(ProviderCache).where(ProviderCache.key==identity).with_for_update().execution_options(populate_existing=True))
    if row.expires>now():result=value(row);db.commit();return result
    pause=db.get(ProviderCache,pause_id,populate_existing=True)
    if pause and pause.expires>now():result={**value(row),'status':pause.status,'stale':row.data is not None};db.commit();return result
    try:
        row.data=fetch(kind,query,platform);row.status='ok';row.fetched=now();row.expires=now()+7*86400
    except ProviderError as error:
        row.status=error.status;row.expires=now()+error.retry
        if error.status in ('blocked','rate_limited'):
            db.execute(insert(ProviderCache).values(key=pause_id,status=error.status,expires=row.expires)
                .on_conflict_do_update(index_elements=['key'],set_={'status':error.status,'expires':row.expires}))
    result=value(row);db.commit();return result

def resolve(db,title,platform,identity=None,refresh=True):
    if not identity and not human_title(title):
        return {'data':None,'game':None,'candidates':[],'fetched':None,'stale':False,'status':'title_unavailable'}
    response=cached(db,'detail' if identity else 'search',identity or search_title(title),platform,refresh)
    game=response['data'] if identity else None
    candidates=[] if identity else (response['data'] or {}).get('games',[])
    if not identity:
        matches=[g for g in candidates if normalized_title(g['title'])==normalized_title(title) and platform in g['platforms']]
        if len(matches)==1:game=matches[0]
    if game and game['platforms'] and platform not in game['platforms']:
        return {**response,'game':None,'candidates':candidates,'status':'mismatch'}
    return {**response,'game':game,'candidates':candidates,
            'status':response['status'] if game or response['status']!='ok' else 'needs_match' if candidates else 'not_found'}
