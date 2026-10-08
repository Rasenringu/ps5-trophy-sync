import hashlib
import json
import os
import secrets
import time
import uuid
from urllib.parse import urlencode, urlsplit
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError
from fastapi import FastAPI, Depends, HTTPException, Request, Response
from sqlalchemy import select, delete, tuple_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DbSession
from .db import database
from .models import Account, Login, Installation, Profile, Pairing, Import, Record, Rate, Artwork, TrophyInfo, TrophyText, DevicePackage, DeviceArtwork
from .locales import choose_language
from .contracts import Credentials, PairRequest, Code, Approval, Poll, Snapshot, NativeSnapshot, NativeActivitySnapshot

app = FastAPI(title='PS5 Trophy Sync', version='0.1.0')
origin = os.environ.get('WEB_ORIGIN', 'http://localhost:3000').rstrip('/')
secure_cookie = os.environ.get('COOKIE_SECURE', 'true') == 'true'
development_tools = os.environ.get('ENABLE_DEVELOPMENT_TOOLS', 'false') == 'true'
if os.environ.get('ENVIRONMENT')=='production':
    parsed_origin=urlsplit(origin)
    if parsed_origin.scheme!='https' or not parsed_origin.hostname or parsed_origin.username or parsed_origin.path or parsed_origin.query or parsed_origin.fragment or not secure_cookie or development_tools:
        raise RuntimeError('Production requires an HTTPS origin, secure cookies and disabled development tools')
ph = PasswordHasher()
dummy_hash = ph.hash(secrets.token_urlsafe(32))
now = lambda: int(time.time())
uid = lambda: str(uuid.uuid4())
digest = lambda value: hashlib.sha256(value.encode()).hexdigest()

def fail(status, detail):
    raise HTTPException(status, detail)

@app.middleware('http')
async def guard(request: Request, call_next):
    # Browser writes require a same-origin request even in local HTTP development.
    if request.method not in ('GET', 'HEAD', 'OPTIONS') and request.url.path.startswith(('/auth/', '/account/')):
        if request.headers.get('origin') != origin:
            return Response('Same-origin request required', status_code=403)
    try:
        length = int(request.headers.get('content-length', '0'))
    except ValueError:
        return Response('Invalid Content-Length', status_code=400)
    if request.url.path=='/device/artwork':
        # Authenticate before accepting a larger streamed native package.
        if length<0 or length>64*1024*1024:
            return Response('Artwork package exceeds bounds',status_code=413)
        response=await call_next(request)
        response.headers['Cache-Control']='no-store'
        response.headers['X-Content-Type-Options']='nosniff'
        return response
    if length > 2_000_000:
        return Response('Snapshot exceeds 2MB', status_code=413)
    if request.method in ('POST', 'PUT', 'PATCH'):
        parts, size = [], 0
        async for chunk in request.stream():
            size += len(chunk)
            if size > 2_000_000:
                return Response('Snapshot exceeds 2MB', status_code=413)
            parts.append(chunk)
        request._body = b''.join(parts)
    response = await call_next(request)
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

def rate(db, key, limit=20, seconds=60):
    # INSERT on conflict and row locks work across workers, unlike process counters.
    from sqlalchemy.dialects.postgresql import insert
    key = digest(key)
    db.execute(insert(Rate).values(key=key, count=0, reset=now()+seconds).on_conflict_do_nothing())
    row = db.scalar(select(Rate).where(Rate.key == key).with_for_update())
    if row.reset <= now():
        row.count, row.reset = 0, now()+seconds
    row.count += 1
    allowed = row.count <= limit
    db.commit()
    if not allowed:
        fail(429, 'Too many attempts; wait before retrying')

def browser(request: Request, db: DbSession = Depends(database)):
    token = request.cookies.get('session', '')
    login = db.get(Login, digest(token))
    if not login or login.expires <= now():
        fail(401, 'Sign in again')
    return login.account

def bearer(request):
    value = request.headers.get('authorization', '')
    if not value.startswith('Bearer ') or len(value) > 200:
        fail(401, 'Credential required')
    return digest(value[7:])

def device(request: Request, db: DbSession = Depends(database)):
    profile = db.scalar(select(Profile).where(Profile.token == bearer(request)).with_for_update())
    if not profile or profile.revoked or not profile.owner:
        fail(401, 'Pair this profile again; credential missing or revoked')
    return profile

def set_login(db, response, account):
    token = secrets.token_urlsafe(32)
    db.add(Login(digest=digest(token), account=account, expires=now()+86400))
    db.commit()
    response.set_cookie('session', token, httponly=True, secure=secure_cookie,
                        samesite='strict', max_age=86400, path='/')

@app.get('/health')
def health(db: DbSession = Depends(database)):
    db.execute(select(Account.id).limit(1))
    return {'status': 'ok', 'console_verified': False}

@app.post('/auth/register', status_code=201)
def register(body: Credentials, request: Request, response: Response, db: DbSession = Depends(database)):
    rate(db, 'register:'+request.client.host, 5, 300)
    account = Account(id=uid(), email=body.email.strip().lower(), password=ph.hash(body.password))
    db.add(account)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        fail(409, 'Account cannot be registered with this email')
    from .social import ensure_social
    ensure_social(db,account.id)
    set_login(db, response, account.id)
    return {'id': account.id, 'email': account.email}

@app.post('/auth/login')
def login(body: Credentials, request: Request, response: Response, db: DbSession = Depends(database)):
    rate(db, 'login:'+request.client.host, 10, 300)
    account = db.scalar(select(Account).where(Account.email == body.email.strip().lower()))
    try:
        ph.verify(account.password if account else dummy_hash, body.password)
    except (VerificationError, InvalidHashError):
        fail(401, 'Email or password is incorrect')
    if not account:
        fail(401, 'Email or password is incorrect')
    set_login(db, response, account.id)
    return {'id': account.id, 'email': account.email}

@app.post('/auth/logout')
def logout(request: Request, response: Response, db: DbSession = Depends(database)):
    db.execute(delete(Login).where(Login.digest == digest(request.cookies.get('session', ''))))
    db.commit()
    response.delete_cookie('session', path='/')
    return {'status': 'signed_out'}

@app.get('/account/me')
def me(owner: str = Depends(browser), db: DbSession = Depends(database)):
    a = db.get(Account, owner)
    return {'id': a.id, 'email': a.email}

@app.post('/device/installations', status_code=201)
def installation(request: Request, db: DbSession = Depends(database)):
    rate(db, 'install:'+request.client.host, 10, 300)
    token, identity = secrets.token_urlsafe(32), uid()
    db.add(Installation(id=identity, digest=digest(token)))
    db.commit()
    return {'installation_id': identity, 'installation_secret': token}

@app.post('/device/pairings', status_code=201)
def start_pairing(body: PairRequest, request: Request, db: DbSession = Depends(database)):
    rate(db, 'pair:'+request.client.host, 10, 300)
    install = db.scalar(select(Installation).where(Installation.id == str(body.installation_id)).with_for_update())
    if not install or not secrets.compare_digest(install.digest, bearer(request)):
        fail(401, 'Installation credential is required')
    profile = db.scalar(select(Profile).where(Profile.installation == install.id, Profile.local_id == body.profile_id).with_for_update())
    if not profile:
        profile = Profile(id=uid(), installation=install.id, local_id=body.profile_id, label=body.profile_label)
        db.add(profile)
        db.flush()
    elif profile.token and not profile.revoked:
        fail(409, 'Revoke the existing credential in device management before relinking')
    # Invalidate previous outstanding authorizations for this profile.
    for old in db.scalars(select(Pairing).where(Pairing.profile == profile.id, Pairing.state.in_(['pending', 'approved']))):
        old.state = 'cancelled'
    code = ''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(8))
    code = code[:4]+'-'+code[4:]
    secret = secrets.token_urlsafe(32)
    p = Pairing(id=uid(), secret=digest(secret), code=digest(code), profile=profile.id, expires=now()+600, next_poll=0)
    db.add(p)
    db.commit()
    return {'pairing_id': p.id, 'device_code': secret, 'user_code': code, 'expires_at': p.expires,
            'interval': 5, 'verification_uri': origin+'/pair',
            'verification_uri_complete': origin+'/pair?'+urlencode({'code': code})}

def find_code(db, code):
    candidate = db.scalar(select(Pairing).where(Pairing.code == digest(code)))
    if not candidate:
        fail(400, 'Code expired or already used; request a new code on the console')
    db.scalar(select(Profile).where(Profile.id == candidate.profile).with_for_update())
    p = db.scalar(select(Pairing).where(Pairing.id == candidate.id).with_for_update().execution_options(populate_existing=True))
    if not p or p.expires <= now() or p.state != 'pending':
        fail(400, 'Code expired or already used; request a new code on the console')
    return p

@app.post('/account/pairings/inspect')
def inspect_code(body: Code, request: Request, owner: str = Depends(browser), db: DbSession = Depends(database)):
    rate(db, 'code:'+owner, 10, 60)
    p = find_code(db, body.code)
    profile = db.get(Profile, p.profile)
    return {'pairing_id': p.id, 'installation_id': profile.installation, 'profile_label': profile.label,
            'profile_id': profile.local_id, 'expires_at': p.expires}

@app.post('/account/pairings/approve')
def approve(body: Approval, owner: str = Depends(browser), db: DbSession = Depends(database)):
    rate(db, 'approve:'+owner, 10, 60)
    p = find_code(db, body.code)
    if p.id != str(body.pairing_id):
        fail(400, 'Pairing changed; inspect the code again')
    profile = db.scalar(select(Profile).where(Profile.id == p.profile).with_for_update())
    if profile.owner and profile.owner != owner:
        fail(403, 'Profile belongs to another account')
    profile.owner = owner
    p.account, p.state = owner, 'approved'
    db.commit()
    return {'status': 'approved'}

@app.post('/device/pairings/poll')
def poll(body: Poll, db: DbSession = Depends(database)):
    candidate = db.scalar(select(Pairing).where(Pairing.secret == digest(body.device_code)))
    if not candidate:
        fail(400, 'Unknown device authorization')
    # Consistent profile -> authorization lock order also used by approval/revoke.
    db.scalar(select(Profile).where(Profile.id == candidate.profile).with_for_update())
    p = db.scalar(select(Pairing).where(Pairing.id == candidate.id).with_for_update().execution_options(populate_existing=True))
    if p.expires <= now():
        fail(410, 'Authorization expired; stop polling and request a new code')
    if p.state in ('consumed', 'cancelled'):
        fail(410, 'Authorization already used or cancelled')
    if p.next_poll > now():
        fail(429, 'Poll no more than once every five seconds')
    p.next_poll = now()+5
    if p.state == 'pending':
        db.commit()
        return {'status': 'pending', 'interval': 5}
    profile = db.scalar(select(Profile).where(Profile.id == p.profile).with_for_update())
    if profile.owner != p.account:
        fail(403, 'Profile ownership changed')
    token = secrets.token_urlsafe(32)
    profile.token, profile.revoked, p.state = digest(token), False, 'consumed'
    db.commit()
    return {'status': 'paired', 'device_token': token, 'profile_uuid': profile.id}

@app.post('/device/status')
def device_status(profile: Profile = Depends(device)):
    return {'status': 'paired', 'profile_uuid': profile.id, 'profile_id': profile.local_id}

@app.get('/account/devices')
def devices(owner: str = Depends(browser), db: DbSession = Depends(database)):
    return [{'id': p.id, 'installation_id': p.installation, 'profile_label': p.label,
             'revoked': p.revoked, 'status': 'revoked' if p.revoked else 'paired' if p.token else 'pending',
             'last_sync': p.last_sync} for p in
            db.scalars(select(Profile).where(Profile.owner == owner,Profile.revoked==False))]

@app.post('/account/devices/{profile_id}/revoke')
def revoke(profile_id: str, owner: str = Depends(browser), db: DbSession = Depends(database)):
    profile = db.scalar(select(Profile).where(Profile.id == profile_id, Profile.owner == owner).with_for_update())
    if not profile:
        fail(404, 'Profile not found')
    profile.revoked, profile.token = True, None
    for p in db.scalars(select(Pairing).where(Pairing.profile == profile_id, Pairing.state.in_(['pending', 'approved']))):
        p.state = 'cancelled'
    db.commit()
    return {'status': 'revoked'}

@app.post('/device/sync')
def sync(body: Snapshot | NativeSnapshot | NativeActivitySnapshot, profile: Profile = Depends(device), db: DbSession = Depends(database)):
    if body.mock and not development_tools:fail(422, 'Demo imports are disabled')
    data = body.model_dump(mode='json')
    checksum = digest(json.dumps(data, sort_keys=True, separators=(',', ':')))
    old = db.scalar(select(Import).where(Import.profile == profile.id, Import.batch_id == str(body.batch_id)))
    if old:
        if old.digest != checksum:
            fail(409, 'Batch ID reused with different contents')
        return {'status': 'duplicate', 'batch_id': str(body.batch_id)}
    for kind, rows in [('trophy', data['trophies']), ('activity', data['activities'])]:
        for row in rows:
            if isinstance(body, NativeSnapshot):
                row['consistency'] = body.consistency
                row['profile_binding'] = body.profile_binding
                row['observed_unlock_state'] = row['unlocked']
            if isinstance(body,NativeActivitySnapshot):
                row['consistency']=body.consistency
                row['profile_binding']=body.profile_binding
            key = json.dumps([row['title_id'], row['trophy_id']], ensure_ascii=False, separators=(',', ':')) if kind == 'trophy' else row['event_id']
            record = db.scalar(select(Record).where(Record.profile == profile.id, Record.source == body.source,
                                 Record.kind == kind, Record.key == key, Record.mock == body.mock))
            if not record:
                db.add(Record(id=uid(), profile=profile.id, source=body.source, kind=kind, key=key, data=row, mock=body.mock))
            else:
                previous = record.data
                if kind == 'trophy' and previous['unlocked']:
                    row['unlocked'] = True
                    row['unlocked_at'] = previous['unlocked_at'] or row['unlocked_at']
                    if previous.get('unlocked_at') and 'clock' in previous:
                        row['clock'] = previous['clock']
                if kind == 'trophy':
                    if row['unlocked'] is None and previous['unlocked'] is not None:
                        row['unlocked'] = previous['unlocked']
                    if 'native_observation' in previous and 'native_observation' not in row:
                        row['native_observation'] = previous['native_observation']
                if kind == 'activity' and previous['complete'] and not row['complete']:
                    continue
                if kind == 'activity' and row.get('duration_basis')=='native_foreground_seconds':
                    # Replayed/cumulative native observations must never reduce totals.
                    if previous.get('duration_basis')=='native_foreground_seconds' and previous.get('duration_seconds') is not None and row.get('duration_seconds') is not None and previous['duration_seconds']>row['duration_seconds']:
                        continue
                record.data = row
    db.add(Import(id=uid(), profile=profile.id, batch_id=str(body.batch_id), digest=checksum, received=now(), mock=body.mock))
    profile.last_sync = now()
    db.commit()
    return {'status': 'imported', 'batch_id': str(body.batch_id), 'mock': body.mock}

@app.get('/account/library')
def library(owner: str = Depends(browser), db: DbSession = Depends(database), language: str = 'en'):
    if not isinstance(language,str) or len(language)>160:
        fail(422,'Invalid language preferences')
    rows = list(db.execute(select(Record, Profile.label).join(Profile, Record.profile == Profile.id).where(Profile.owner == owner,Profile.revoked==False)))
    if not development_tools:rows=[(r,label) for r,label in rows if not r.mock]
    # Sony application IDs and trophy-set IDs are separate namespaces. Join only
    # an unambiguous exact metadata title inside the same owned console profile.
    names={}
    for record,_ in rows:
        if not record.mock and record.source=='ps5_native' and record.kind=='trophy':
            names.setdefault((record.profile,record.data['title']),set()).add(record.data['title_id'])
    aliases={record.id:next(iter(names[(record.profile,record.data['title'])]))
             for record,_ in rows if not record.mock and record.kind=='activity'
             and record.source=='ps5_native' and record.data.get('duration_basis')=='native_foreground_seconds'
             and len(names.get((record.profile,record.data['title']),set()))==1}
    trophy_games={(r.profile,r.source,r.mock,r.data['title_id']) for r,_ in rows if r.kind=='trophy'}
    rows=[(r,label) for r,label in rows if (r.profile,r.source,r.mock,aliases.get(r.id,r.data['title_id'])) in trophy_games]
    titles = {r.data['title_id'] for r, _ in rows if not r.mock}
    titles.update(aliases.values())
    # The library response needs URLs, never the cached PNG bodies.
    images = {(source,title,trophy): '/api/account/artwork/'+identity
              for source,title,trophy,identity in db.execute(select(Artwork.source,Artwork.title_id,Artwork.trophy_id,Artwork.id).where(Artwork.title_id.in_(titles)))} if titles else {}
    info = {(i.source,i.title_id,i.trophy_id): i for i in db.scalars(select(TrophyInfo).where(TrophyInfo.title_id.in_(titles)))} if titles else {}
    languages={}
    for source,title,locale,is_default in db.execute(select(TrophyText.source,TrophyText.title_id,TrophyText.language,TrophyText.is_default).where(TrophyText.title_id.in_(titles),TrophyText.trophy_id=='')):
        entry=languages.setdefault((source,title),{'available':[],'default':'en-US'})
        entry['available'].append(locale)
        if is_default:
            entry['default']=locale
    choices={(source,title):choose_language(value['available'],language,value['default']) for (source,title),value in languages.items()}
    selected=[(source,title,locale) for (source,title),locale in choices.items()]
    translations={(v.source,v.title_id,v.trophy_id):v for v in db.scalars(select(TrophyText).where(tuple_(TrophyText.source,TrophyText.title_id,TrophyText.language).in_(selected)))} if selected else {}
    packages={(p.profile,p.title_id):p for p in db.scalars(select(DevicePackage).where(DevicePackage.profile.in_({r.profile for r,_ in rows}),DevicePackage.title_id.in_(titles)))} if titles else {}
    scoped_images={(p,t,trophy):'/api/account/device-artwork/'+identity for p,t,trophy,identity in db.execute(select(DeviceArtwork.profile,DeviceArtwork.title_id,DeviceArtwork.trophy_id,DeviceArtwork.id).where(DeviceArtwork.profile.in_({r.profile for r,_ in rows}),DeviceArtwork.title_id.in_(titles)))} if titles else {}
    result = []
    for r, label in rows:
        title=aliases.get(r.id,r.data['title_id'])
        key = (r.source,title,r.data.get('trophy_id',''))
        metadata = None if r.mock else info.get(key)
        data = dict(r.data)
        if r.id in aliases:
            data['title_id']=title
            data['title_binding']='unique_local_title_metadata'
        earned = data.get('unlocked') is True
        translated=None if r.mock or r.kind!='trophy' else translations.get(key)
        translated_game=None if r.mock else translations.get((r.source,title,''))
        if translated_game:
            data['title']=translated_game.name
        if translated:
            data['name']=translated.name
        if metadata:
            data['hidden'] = metadata.hidden
            data['description'] = (translated.description if translated else metadata.description) if earned or not metadata.hidden else None
            if metadata.hidden and not earned:
                data['name'] = 'Hidden trophy'
        package=None if r.mock or r.source!='ps5_native' else packages.get((r.profile,title))
        package_language=None
        if package:
            bundle=package.metadata_json
            package_language=choose_language(list(bundle['texts']),language,bundle['default'])
            text=bundle['texts'][package_language]
            data['title']=text[''][0]
            if r.kind=='trophy' and data['trophy_id'] in bundle['info']:
                hidden,description=bundle['info'][data['trophy_id']]
                data['hidden']=hidden
                data['name']=text[data['trophy_id']][0] if earned or not hidden else 'Hidden trophy'
                data['description']=text[data['trophy_id']][1] if earned or not hidden else None
        result.append({'profile_uuid':r.profile,'profile_label':label,'source':r.source,'kind':r.kind,
            'mock':r.mock,'data':data,'content_language':None if r.mock else package_language or choices.get((r.source,title)),
            'artwork_url':None if r.mock else scoped_images.get((r.profile,title,'')) or images.get((r.source,title,'')),
            'icon_url':None if r.mock or not earned else scoped_images.get((r.profile,title,data.get('trophy_id',''))) or images.get(key)})
    return result

@app.get('/account/artwork/{artwork_id}')
def artwork(artwork_id: str, request: Request, owner: str = Depends(browser), db: DbSession = Depends(database)):
    image = db.get(Artwork, artwork_id)
    if image is None:
        fail(404, 'Artwork unavailable')
    owned = select(Record.id).join(Profile, Record.profile == Profile.id).where(
        Profile.owner == owner, Profile.revoked==False, Record.mock == False, Record.source == image.source,
        Record.kind == 'trophy', Record.data['title_id'].as_string() == image.title_id)
    if image.trophy_id:
        owned = owned.where(Record.data['trophy_id'].as_string() == image.trophy_id,
                            Record.data['unlocked'].as_boolean() == True)
    if db.scalar(owned.limit(1)) is None:
        fail(404, 'Artwork unavailable')
    headers = {'Cache-Control': 'private, no-cache', 'Vary': 'Cookie', 'ETag': '"'+image.digest+'"',
               'X-Content-Type-Options': 'nosniff'}
    if request.headers.get('if-none-match') == headers['ETag']:
        return Response(status_code=304, headers=headers)
    return Response(image.content, media_type='image/png', headers=headers)


from .contracts import Strict
from pydantic import Field
class ArtworkCheck(Strict):
    title_id: str=Field(pattern=r'^NPWR[0-9]{5}_00$')
    sha256: str=Field(pattern=r'^[0-9a-f]{64}$')

@app.post('/device/artwork/check')
def artwork_check(body: ArtworkCheck, profile: Profile=Depends(device), db: DbSession=Depends(database)):
    rate(db,'artwork-check:'+profile.id,256,600)
    known=db.scalar(select(Record.id).where(Record.profile==profile.id,Record.mock==False,
        Record.source=='ps5_native',Record.kind=='trophy',Record.data['title_id'].as_string()==body.title_id).limit(1))
    if not known:fail(403,'Import this profile trophy set before its artwork')
    package=db.get(DevicePackage,(profile.id,body.title_id))
    return {'needed':package is None or package.digest!=body.sha256}

@app.post('/device/artwork')
async def device_artwork(request: Request, profile: Profile=Depends(device), db: DbSession=Depends(database)):
    rate(db,'artwork-upload:'+profile.id,32,600)
    if request.headers.get('content-type')!='application/octet-stream':fail(415,'Native UCP package required')
    parts=[];size=0
    async for chunk in request.stream():
        size+=len(chunk)
        if size>64*1024*1024:fail(413,'Artwork package exceeds bounds')
        parts.append(chunk)
    current=db.scalar(select(Profile).where(Profile.id==profile.id).with_for_update().execution_options(populate_existing=True))
    if not current or current.revoked or current.token!=bearer(request) or not current.owner:fail(401,'Pair this profile again; credential missing or revoked')
    from .device_artwork import store_package
    try:title,sha=store_package(db,profile.id,b''.join(parts))
    except PermissionError as error:fail(403,str(error))
    except (ValueError,KeyError,TypeError,UnicodeError,OverflowError):fail(422,'Invalid native artwork package')
    db.commit()
    return {'status':'stored','title_id':title,'sha256':sha}

@app.get('/account/device-artwork/{identity}')
def device_image(identity: str, request: Request, owner: str=Depends(browser), db: DbSession=Depends(database)):
    image=db.scalar(select(DeviceArtwork).join(Profile,Profile.id==DeviceArtwork.profile).where(DeviceArtwork.id==identity,Profile.owner==owner,Profile.revoked==False))
    if image is None:fail(404,'Artwork unavailable')
    owned=select(Record.id).where(Record.profile==image.profile,Record.source=='ps5_native',Record.mock==False,
        Record.kind=='trophy',Record.data['title_id'].as_string()==image.title_id)
    if image.trophy_id:owned=owned.where(Record.data['trophy_id'].as_string()==image.trophy_id,Record.data['unlocked'].as_boolean()==True)
    if db.scalar(owned.limit(1)) is None:fail(404,'Artwork unavailable')
    headers={'Cache-Control':'private, no-cache','Vary':'Cookie','ETag':'"'+image.digest+'"','X-Content-Type-Options':'nosniff'}
    if request.headers.get('if-none-match')==headers['ETag']:return Response(status_code=304,headers=headers)
    return Response(image.content,media_type='image/png',headers=headers)


from .social import router as social_router
app.include_router(social_router)
