"""Independent client for the documented PlatPrices v2 API; no scraped pages.

Only numeric rates leave this adapter. Provider text never replaces console
metadata. list_id is an opaque provider ID, not an NPWR communication ID.
"""
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from email.utils import parsedate_to_datetime
import hashlib
import os
import re
import time
import unicodedata
import httpx
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from .models import ProviderCache

BASE = 'https://platprices.com/api/v2'
MAX_BODY = 512 * 1024

def settings():
    key = os.environ.get('PLATPRICES_API_KEY', '').strip()
    region = os.environ.get('PLATPRICES_REGION', 'us').lower()
    return key, region

def configured():
    key, region = settings()
    return bool(key) and re.fullmatch('[a-z]{2}', region) is not None

class ProviderError(Exception):
    def __init__(self, status='unavailable', retry=3600):
        self.status, self.retry = status, retry

def retry_seconds(value):
    try:
        seconds = int(value)
    except (ValueError, TypeError):
        try:
            seconds = int(parsedate_to_datetime(value).timestamp() - time.time())
        except (ValueError, TypeError, OverflowError):
            seconds = 3600
    return min(31*86400, max(60, seconds))

def request_json(path, params, key):
    """Fixed origin, verified TLS, no redirects, streaming body/deadline bounds."""
    deadline = time.monotonic() + 10
    try:
        with httpx.Client(timeout=httpx.Timeout(5, connect=3), follow_redirects=False,
                          trust_env=False, headers={'X-API-Key': key, 'Accept': 'application/json',
                          'User-Agent': 'TrophySync/0.1'}) as client:
            with client.stream('GET', BASE + path, params=params) as response:
                if response.status_code == 429:
                    raise ProviderError('rate_limited', retry_seconds(response.headers.get('retry-after')))
                if response.status_code in (401, 403):
                    raise ProviderError('configuration_error')
                if response.status_code == 404:
                    raise ProviderError('not_found', 86400)
                if response.status_code != 200:
                    raise ProviderError()
                if response.headers.get('content-type', '').split(';')[0].strip() != 'application/json':
                    raise ProviderError('invalid_response')
                chunks, size = [], 0
                for chunk in response.iter_bytes():
                    size += len(chunk)
                    if size > MAX_BODY or time.monotonic() > deadline:
                        raise ProviderError('invalid_response')
                    chunks.append(chunk)
                import json
                value = json.loads(b''.join(chunks))
                if not isinstance(value, dict) or value.get('success') is not True or 'data' not in value:
                    raise ProviderError('invalid_response')
                return value['data']
    except (httpx.HTTPError, ValueError, RecursionError):
        raise ProviderError() from None

def cache_key(*parts):
    return hashlib.sha256('\0'.join(parts).encode()).hexdigest()

def cached(db, path, params, fetch=True):
    from .main import now, rate
    key, region = settings()
    if not configured():
        return {'status': 'not_configured', 'data': None, 'fetched': None, 'stale': False}
    credential = cache_key(key)
    identity = cache_key(credential, region, path, repr(sorted(params.items())))
    pause_id = cache_key(credential, 'pause')
    if not fetch:
        row=db.get(ProviderCache,identity)
        return {'status':row.status if row else 'not_cached', 'data':row.data if row else None,
                'fetched':row.fetched if row else None,
                'stale':bool(row and row.data is not None and (row.status!='ok' or row.expires<=now()))}
    # Insert/row locks serialize a cold cache across API workers. The lock is
    # held only for one bounded HTTP call. Cookies and user IDs are never sent.
    db.execute(insert(ProviderCache).values(key=identity, status='unavailable', expires=0).on_conflict_do_nothing())
    row = db.scalar(select(ProviderCache).where(ProviderCache.key==identity).with_for_update().execution_options(populate_existing=True))
    def result():
        return {'status': row.status, 'data': row.data, 'fetched': row.fetched,
                'stale': row.data is not None and row.status != 'ok'}
    if row.expires > now():
        value = result(); db.commit(); return value
    pause = db.get(ProviderCache, pause_id)
    if pause and pause.expires > now():
        value = {**result(), 'status': pause.status, 'stale': row.data is not None}
        db.commit(); return value
    # Separate bounded monthly budget, shared across viewers and API workers.
    # rate() commits; reacquire the cache lock before starting the request.
    db.commit()
    month = datetime.now(timezone.utc).strftime('%Y-%m')
    try:
        rate(db, 'platprices-budget:'+credential+month, 900, 31*86400)
    except HTTPException as error:
        if error.status_code != 429: raise
        return {**result(), 'status': 'rate_limited', 'stale': row.data is not None}
    row = db.scalar(select(ProviderCache).where(ProviderCache.key==identity).with_for_update().execution_options(populate_existing=True))
    if row.expires > now():
        value = result(); db.commit(); return value
    pause=db.get(ProviderCache,pause_id,populate_existing=True)
    if pause and pause.expires>now():
        value={**result(),'status':pause.status,'stale':row.data is not None}
        db.commit();return value
    try:
        payload = request_json(path, {**params, 'region': region}, key)
        # Cache only the limited fields used by this integration.
        row.data = sanitize(path, payload)
        row.status, row.fetched, row.expires = 'ok', now(), now()+86400
    except ProviderError as error:
        row.status, row.expires = error.status, now()+error.retry
        if error.status in ('rate_limited', 'configuration_error'):
            db.execute(insert(ProviderCache).values(key=pause_id, status=error.status, expires=row.expires)
                       .on_conflict_do_update(index_elements=['key'], set_={'status': error.status, 'expires': row.expires}))
    value = result(); db.commit(); return value

def integer(value, minimum=0, maximum=2**31-1):
    if isinstance(value, bool): raise ProviderError('invalid_response')
    if isinstance(value, str) and re.fullmatch(r'\d{1,10}', value): value=int(value)
    if not isinstance(value, int) or not minimum <= value <= maximum:
        raise ProviderError('invalid_response')
    return value

def game(value):
    if not isinstance(value, dict): raise ProviderError('invalid_response')
    ppid=integer(value.get('PPID'), 1)
    # Both names are present in the inspected keyless v2 catalogue response.
    name=value.get('GameName') or value.get('ProductName')
    if not isinstance(name, str) or not 1 <= len(name) <= 400: raise ProviderError('invalid_response')
    ps5=integer(value.get('IsPS5'),0,1)
    return {'id': ppid, 'title': name, 'platform': 'PS5' if ps5 else 'PS4',
            'url': 'https://platprices.com/game/'+str(ppid)}

def sanitize(path, value):
    if path=='/games/search':
        if not isinstance(value, list) or len(value)>25: raise ProviderError('invalid_response')
        return {'games': [game(item) for item in value]}
    if path.endswith('/trophies'):
        if not isinstance(value, dict) or not isinstance(value.get('trophies'),list) or len(value['trophies'])>2500:
            raise ProviderError('invalid_response')
        rows=[]; ids=set()
        for item in value['trophies']:
            if not isinstance(item,dict):raise ProviderError('invalid_response')
            identity=integer(item.get('id'))
            if identity in ids: raise ProviderError('invalid_response')
            ids.add(identity)
            name, grade = item.get('name'), item.get('grade')
            if not isinstance(name,str) or not 1<=len(name)<=400 or grade not in ('bronze','silver','gold','platinum'):
                raise ProviderError('invalid_response')
            rate=item.get('earned_rate')
            if rate is not None:
                try:
                    if isinstance(rate,bool):raise InvalidOperation
                    rate=Decimal(str(rate))
                    if not rate.is_finite() or not 0<=rate<=100: raise InvalidOperation
                    rate=float(rate)
                except (InvalidOperation,ValueError):raise ProviderError('invalid_response') from None
            rows.append({'id': identity, 'name':name, 'grade':grade, 'rate':rate})
        if integer(value.get('total'))!=len(rows):raise ProviderError('invalid_response')
        return {'ppid':integer(value.get('ppid'),1), 'trophies':rows}
    return game(value)

def normalized(value):
    return ''.join(c for c in unicodedata.normalize('NFKC',value).casefold() if c.isalnum())

def match_rates(provider, rows):
    """Bind by unique publisher names AND grades, never by provider ordinal.

    All returned base-game trophies must match. DLC absent from the provider
    stays unknown. The owner explicitly selects the external listing; this is
    not a claim that the provider exposes an exact native trophy-set identity.
    """
    local={}
    for row in rows:
        if row['kind']!='trophy':continue
        data=row['data']; identity=str(data['trophy_id'])
        key=(normalized(data.get('name') or ''),data.get('grade'))
        local.setdefault(key,set()).add(identity)
    result={}
    if not provider['trophies']:return None
    for trophy in provider['trophies']:
        key=(normalized(trophy['name']),trophy['grade'])
        candidates=local.get(key,set())
        if not key[0] or len(candidates)!=1:return None
        identity=next(iter(candidates))
        if identity in result:return None
        result[identity]=trophy['rate']
    return result
