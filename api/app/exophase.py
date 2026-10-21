"""Keyless, user-selected public trophy listings; no automated search.

Independent parser of the public page contract recorded in SOURCES.md. Provider
IDs are opaque. Only verified numerical rates are exposed by insights.py.
"""
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
import re
import time
import httpx
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from .models import ProviderCache
from .platprices import ProviderError, cache_key, retry_seconds

BASE='https://www.exophase.com'
SLUG=r'[a-z0-9]+(?:-[a-z0-9]+)*'
MAX_BODY=2*1024*1024

def listing_slug(url):
    match=re.fullmatch(r'https://www\.exophase\.com/game/('+SLUG+r')/trophies/?',url)
    if not match or len(match[1])>250:raise ProviderError('invalid_listing')
    return match[1]

class ListingParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title=None;self.platforms=set();self.rows=[];self.current=None
        self.in_name=False;self.strong=False;self.last_strong='';self.total=None

    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs);classes=attrs.get('class','').split()
        if tag=='meta' and attrs.get('property')=='og:title':self.title=attrs.get('content')
        if tag=='ul' and 'trophy' in classes:
            self.platforms.update(p for p in ('PS4','PS5') if 'platform-'+p.lower() in classes)
        if tag=='strong':self.strong=True;self.last_strong=''
        if tag=='li' and 'award' in classes:
            if self.current is not None:raise ProviderError('invalid_response')
            rate=attrs.get('data-average')
            try:
                value=Decimal(rate) if rate is not None else None
                if value is not None and (not value.is_finite() or not 0<=value<=100):raise InvalidOperation
            except (InvalidOperation,ValueError):raise ProviderError('invalid_response') from None
            identity=attrs.get('data-master','')
            if not re.fullmatch(r'[1-9][0-9]{0,12}',identity):raise ProviderError('invalid_response')
            self.current={'id':identity,'name':'','grade':None,'rate':float(value) if value is not None else None}
        if self.current is not None:
            if tag=='div' and 'award-title' in classes:self.in_name=True
            if tag=='i':
                grades=[g for g in ('bronze','silver','gold','platinum') if 'exo-icon-trophy-'+g in classes]
                if len(grades)==1:self.current['grade']=grades[0]

    def handle_data(self,data):
        if self.strong:self.last_strong+=data
        if data.strip()=='Total Trophies':
            try:self.total=int(self.last_strong.replace(',','').strip())
            except ValueError:raise ProviderError('invalid_response') from None
        if self.current is not None and self.in_name:self.current['name']+=data

    def handle_endtag(self,tag):
        if tag=='strong':self.strong=False
        if tag=='div':self.in_name=False
        if tag=='li' and self.current is not None:
            self.current['name']=' '.join(self.current['name'].split())
            self.rows.append(self.current);self.current=None

def parse(raw,slug):
    parser=ListingParser()
    try:parser.feed(raw.decode('utf-8',errors='strict'));parser.close()
    except (UnicodeError,ValueError,RecursionError):raise ProviderError('invalid_response') from None
    rows=parser.rows
    if (parser.current is not None or len(parser.platforms)!=1 or not isinstance(parser.title,str)
        or not 1<=len(parser.title)<=400 or not 1<=len(rows)<=2500 or parser.total!=len(rows)
        or len({r['id'] for r in rows})!=len(rows)
        or any(not 1<=len(r['name'])<=400 or r['grade'] is None for r in rows)):
        raise ProviderError('invalid_response')
    return {'listing':{'id':slug,'title':parser.title,'platform':next(iter(parser.platforms)),
                       'url':BASE+'/game/'+slug+'/trophies/'},'trophies':rows}

def fetch(slug):
    if not re.fullmatch(SLUG,slug) or len(slug)>250:raise ProviderError('invalid_listing')
    deadline=time.monotonic()+12
    try:
        with httpx.Client(timeout=httpx.Timeout(6,connect=3),follow_redirects=False,trust_env=False,
                          headers={'User-Agent':'TrophySync/0.1','Accept-Encoding':'identity'}) as client:
            with client.stream('GET',BASE+'/game/'+slug+'/trophies/') as response:
                if response.status_code==429:raise ProviderError('rate_limited',retry_seconds(response.headers.get('retry-after')))
                if response.status_code in (401,403):raise ProviderError('blocked')
                if response.status_code==404:raise ProviderError('not_found',86400)
                if response.status_code!=200:raise ProviderError()
                if response.headers.get('content-type','').split(';')[0].strip().lower()!='text/html':raise ProviderError('invalid_response')
                chunks=[];size=0
                for chunk in response.iter_bytes():
                    size+=len(chunk)
                    if size>MAX_BODY or time.monotonic()>deadline:raise ProviderError('invalid_response')
                    chunks.append(chunk)
                return parse(b''.join(chunks),slug)
    except httpx.HTTPError:raise ProviderError() from None

def cached(db,slug,refresh=True):
    from .main import now,rate
    identity=cache_key('exophase-v1',slug);pause_id=cache_key('exophase-v1','pause')
    def value(row):
        return {'data':row.data if row else None,'fetched':row.fetched if row else None,
                'status':row.status if row else 'not_cached',
                'stale':bool(row and row.data is not None and (row.status!='ok' or row.expires<=now()))}
    if not refresh:return value(db.get(ProviderCache,identity))
    db.execute(insert(ProviderCache).values(key=identity,status='unavailable',expires=0).on_conflict_do_nothing())
    row=db.scalar(select(ProviderCache).where(ProviderCache.key==identity).with_for_update().execution_options(populate_existing=True))
    if row.expires>now():result=value(row);db.commit();return result
    db.commit()
    try:rate(db,'exophase-upstream',10,60)
    except HTTPException as error:
        if error.status_code!=429:raise
        return {**value(row),'status':'rate_limited','stale':row.data is not None}
    row=db.scalar(select(ProviderCache).where(ProviderCache.key==identity).with_for_update().execution_options(populate_existing=True))
    if row.expires>now():result=value(row);db.commit();return result
    pause=db.get(ProviderCache,pause_id,populate_existing=True)
    if pause and pause.expires>now():result={**value(row),'status':pause.status,'stale':row.data is not None};db.commit();return result
    try:
        row.data=fetch(slug);row.status='ok';row.fetched=now();row.expires=now()+86400
    except ProviderError as error:
        row.status=error.status;row.expires=now()+error.retry
        if error.status in ('blocked','rate_limited'):
            db.execute(insert(ProviderCache).values(key=pause_id,status=error.status,expires=row.expires)
                .on_conflict_do_update(index_elements=['key'],set_={'status':error.status,'expires':row.expires}))
    result=value(row);db.commit();return result
