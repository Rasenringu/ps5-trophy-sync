"""Synthetic contract fixtures only; no test claims PS5 extraction validation."""
import os
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from app.db import Base, engine, Session
from app.main import app, digest
from app.models import Pairing, Profile, Installation, Login, Rate

@pytest.fixture(autouse=True)
def reset():
    assert engine.url.database.endswith('_test'), 'Refuse to reset a non-test database'
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

def browser(email='a@example.test'):
    c = TestClient(app, headers={'origin':'http://localhost:3000'})
    r = c.post('/auth/register', json={'email':email,'password':'test-password-123'})
    assert r.status_code == 201, r.text
    return c

def begin(client, local='one', installation=None):
    i = installation or client.post('/device/installations').json()
    p = client.post('/device/pairings', headers={'authorization':'Bearer '+i['installation_secret']},
                    json={'installation_id':i['installation_id'],'profile_id':local,'profile_label':'MOCK '+local})
    assert p.status_code == 201, p.text
    return i, p.json()

def approve(client, p):
    info = client.post('/account/pairings/inspect', json={'code':p['user_code']})
    assert info.status_code == 200
    return client.post('/account/pairings/approve', json={'code':p['user_code'],
                         'pairing_id':info.json()['pairing_id'],'physical_possession':True})

def paired(client, local='one', installation=None):
    i,p = begin(client,local,installation)
    assert approve(client,p).status_code == 200
    r = client.post('/device/pairings/poll', json={'device_code':p['device_code']})
    assert r.status_code == 200, r.text
    return i,p,r.json()

def sample():
    return {'schema_version':1,'batch_id':str(uuid.uuid4()),'source':'ps5_native','mock':True,
            'trophies':[{'title_id':'MOCK001','title':'MOCK GAME','trophy_id':'0','name':'MOCK trophy',
                        'grade':'gold','unlocked':True,'unlocked_at':None}],
            'activities':[{'event_id':'MOCK_SESSION_1','title_id':'MOCK001','title':'MOCK GAME',
                           'duration_seconds':100,'complete':True,'clock':'uncertain'}]}

def upload(c, token, body):
    return c.post('/device/sync',headers={'authorization':'Bearer '+token},json=body)

def native_sample():
    s=sample()
    s.update(schema_version=2, activities=[], consistency='stable_read_not_atomic',
             profile_binding='foreground_user_path_scoped')
    s['trophies'][0].update(clock='uncertain', unlocked_at='2026-10-06T22:07:00Z',
        native_observation={'raw_flags':17,'first_raw':'63926921220000000','second_raw':'63926921220000000'})
    return s

def test_native_unknown_and_candidate_times_are_preserved():
    c=browser();_,_,t=paired(c);s=native_sample()
    assert upload(c,t['device_token'],s).json()['status']=='imported'
    assert upload(c,t['device_token'],s).json()['status']=='duplicate'
    s['batch_id']=str(uuid.uuid4())
    s['trophies'][0].update(unlocked=None,unlocked_at=None,clock='unknown',
        native_observation={'raw_flags':16,'first_raw':'0','second_raw':'63926921220000000'})
    assert upload(c,t['device_token'],s).status_code==200
    row=c.get('/account/library').json()[0]['data']
    assert row['unlocked'] is True and row['clock']=='uncertain'
    assert row['unlocked_at']=='2026-10-06T22:07:00Z'
    assert row['native_observation']['raw_flags']==16
    s['batch_id']=str(uuid.uuid4());s['trophies'][0]['trophy_id']='unknown'
    assert upload(c,t['device_token'],s).status_code==200
    rows=c.get('/account/library').json()
    assert next(r['data'] for r in rows if r['data']['trophy_id']=='unknown')['unlocked'] is None
    assert len(rows)==2

def test_native_v2_rejects_false_states_and_unsupported_claims():
    c=browser();_,_,t=paired(c)
    for change in ({'clock':'trusted'}, {'unlocked':False},
                   {'native_observation':{'raw_flags':16,'first_raw':'0','second_raw':'1'}}):
        s=native_sample();s['trophies'][0].update(change)
        assert upload(c,t['device_token'],s).status_code==422
    for change in ({'consistency':'atomic'}, {'source':'ps4_bc'}, {'activities':sample()['activities']}):
        s=native_sample();s.update(change)
        assert upload(c,t['device_token'],s).status_code==422

def test_native_v1_checksum_stays_unchanged():
    import json
    from app.contracts import Snapshot
    from app.models import Import
    c=browser();_,_,t=paired(c);s=sample()
    assert upload(c,t['device_token'],s).status_code==200
    expected=digest(json.dumps(Snapshot.model_validate(s).model_dump(mode='json'),sort_keys=True,separators=(',',':')))
    with Session() as db:
        row=db.scalar(select(Import).where(Import.batch_id==s['batch_id']))
        assert row.digest==expected
    assert upload(c,t['device_token'],s).json()['status']=='duplicate'

def test_auth_csrf_logout_and_private():
    c=browser()
    assert c.get('/account/me').status_code==200
    assert c.post('/auth/logout',headers={'origin':'https://evil.test'}).status_code==403
    assert c.post('/auth/logout').status_code==200
    assert c.get('/account/library').status_code==401
    assert c.post('/auth/login',json={'email':'a@example.test','password':'wrong-password'}).status_code==401
    assert c.post('/auth/login',json={'email':'a@example.test','password':'test-password-123'}).status_code==200
    with Session() as db:
        session=c.cookies.get('session')
        assert db.get(Login,digest(session))
        assert not db.get(Login,session)

def test_origin_rejection_is_json_and_never_creates_account():
    from app.models import Account
    c=TestClient(app)
    body={'email':'origin-check@example.test','password':'test-password-123'}
    for headers in ({}, {'origin':'null'}, {'origin':'https://evil.test'}, {'origin':'https://['}):
        response=c.post('/auth/register',json=body,headers=headers)
        assert response.status_code==403
        assert response.json()=={'detail':'Same-origin request required','code':'origin_mismatch',
                                 'website_url':'http://localhost:3000'}
        assert response.headers['cache-control']=='no-store'
    with Session() as db:
        assert db.scalar(select(Account).where(Account.email==body['email'])) is None

def test_device_status_requires_own_scoped_unrevoked_credential():
    c=browser();i,p,t=paired(c,local='MOCK_STATUS')
    assert c.post('/device/status',json={}).status_code==401
    assert c.post('/device/status',headers={'authorization':'Bearer '+i['installation_secret']},json={}).status_code==401
    response=c.post('/device/status',headers={'authorization':'Bearer '+t['device_token']},json={})
    assert response.status_code==200
    assert response.json()=={'status':'paired','profile_uuid':t['profile_uuid'],'profile_id':'MOCK_STATUS'}
    assert t['device_token'] not in response.text and p['device_code'] not in response.text
    c.post('/account/devices/'+t['profile_uuid']+'/revoke',json={})
    assert c.post('/device/status',headers={'authorization':'Bearer '+t['device_token']},json={}).status_code==401

def test_installation_and_single_use_secrets():
    c=browser(); i,p,t=paired(c)
    assert i['installation_secret'] not in p['verification_uri_complete']
    assert p['device_code'] not in p['verification_uri_complete']
    assert t['device_token'] not in p['verification_uri_complete']
    assert c.post('/device/pairings/poll',json={'device_code':p['device_code']}).status_code==410
    with Session() as db:
        assert db.get(Installation,i['installation_id']).digest==digest(i['installation_secret'])
        assert db.get(Profile,t['profile_uuid']).token==digest(t['device_token'])
    r=c.post('/device/pairings',headers={'authorization':'Bearer '+t['device_token']},json={
        'installation_id':i['installation_id'],'profile_id':'two','profile_label':'MOCK'})
    assert r.status_code==401

def test_poll_bound_and_expiry():
    c=browser(); i,p=begin(c)
    assert c.post('/device/pairings/poll',json={'device_code':p['device_code']}).json()['status']=='pending'
    assert c.post('/device/pairings/poll',json={'device_code':p['device_code']}).status_code==429
    with Session() as db:
        row=db.get(Pairing,p['pairing_id']);row.expires=0;db.commit()
    assert approve_expired(c,p).status_code==400
    assert c.post('/device/pairings/poll',json={'device_code':p['device_code']}).status_code==410

def approve_expired(c,p):
    return c.post('/account/pairings/inspect',json={'code':p['user_code']})

def test_approval_needs_inspection_and_possession():
    c=browser();i,p=begin(c)
    assert c.post('/account/pairings/approve',json={'code':p['user_code'],'pairing_id':p['pairing_id'],'physical_possession':False}).status_code==422
    assert c.post('/account/pairings/approve',json={'code':p['user_code'],'pairing_id':str(uuid.uuid4()),'physical_possession':True}).status_code==400

def test_isolation_and_revocation_relink():
    a=browser(); b=browser('b@example.test');i,p,t=paired(a)
    assert upload(a,t['device_token'],sample()).status_code==200
    assert b.get('/account/library').json()==[]
    assert b.get('/account/devices').json()==[]
    assert b.post('/account/devices/'+t['profile_uuid']+'/revoke').status_code==404
    assert a.post('/account/devices/'+t['profile_uuid']+'/revoke').status_code==200
    assert upload(a,t['device_token'],sample()).status_code==401
    _,p2=begin(a,installation=i)
    assert approve(b,p2).status_code==403
    assert approve(a,p2).status_code==200

def test_two_profiles_same_installation_and_local_id_different_installations():
    a=browser();b=browser('b@example.test'); i,p,t=paired(a)
    _,p2,t2=paired(b,'two',i)
    _,p3,t3=paired(b,'one')
    assert len({t['profile_uuid'],t2['profile_uuid'],t3['profile_uuid']})==3
    assert upload(a,t['device_token'],sample()).status_code==200
    assert b.get('/account/library').json()==[]

def test_idempotency_snapshot_sessions_and_non_destructive_absence():
    c=browser();_,_,t=paired(c);data=sample()
    assert upload(c,t['device_token'],data).json()['status']=='imported'
    assert upload(c,t['device_token'],data).json()['status']=='duplicate'
    changed={**data,'trophies':[]}
    assert upload(c,t['device_token'],changed).status_code==409
    data['batch_id']=str(uuid.uuid4())
    assert upload(c,t['device_token'],data).status_code==200
    assert len(c.get('/account/library').json())==2
    empty={**data,'batch_id':str(uuid.uuid4()),'trophies':[],'activities':[]}
    assert upload(c,t['device_token'],empty).status_code==200
    assert len(c.get('/account/library').json())==2

def test_monotonic_trophy_and_session_evidence():
    c=browser();_,_,t=paired(c);data=sample()
    data['trophies'][0]['unlocked_at']='2026-01-01T00:00:00Z'
    assert upload(c,t['device_token'],data).status_code==200
    data['batch_id']=str(uuid.uuid4());data['trophies'][0].update(unlocked=False,unlocked_at=None)
    data['activities'][0].update(complete=False,duration_seconds=None)
    assert upload(c,t['device_token'],data).status_code==200
    rows=c.get('/account/library').json()
    trophy=next(r['data'] for r in rows if r['kind']=='trophy')
    activity=next(r['data'] for r in rows if r['kind']=='activity')
    assert trophy['unlocked'] and trophy['unlocked_at']=='2026-01-01T00:00:00Z'
    assert activity['complete'] and activity['duration_seconds']==100

def test_native_ps4_and_mock_namespaces():
    c=browser();_,_,t=paired(c);data=sample()
    assert upload(c,t['device_token'],data).status_code==200
    data.update(batch_id=str(uuid.uuid4()),source='ps4_bc')
    assert upload(c,t['device_token'],data).status_code==200
    data.update(batch_id=str(uuid.uuid4()),mock=False)
    assert upload(c,t['device_token'],data).status_code==200
    assert len(c.get('/account/library').json())==6

def test_parser_validation_unknown_timestamps_and_duplicate_keys():
    c=browser();_,_,t=paired(c);data=sample()
    data['activities'][0].update(complete=False,duration_seconds=100)
    assert upload(c,t['device_token'],data).status_code==422
    data=sample();data['trophies']*=2
    assert upload(c,t['device_token'],data).status_code==422
    data=sample();data['trophies'][0]['unlocked_at']='2026-01-01T00:00:00'
    assert upload(c,t['device_token'],data).status_code==422
    data=sample();data['activities'][0]['started_at']='2026-01-02T00:00:00Z';data['activities'][0]['ended_at']='2026-01-01T00:00:00Z'
    assert upload(c,t['device_token'],data).status_code==422

def test_rate_limit_persisted_and_cookie_flags():
    c=TestClient(app,headers={'origin':'http://localhost:3000'})
    for _ in range(10):
        assert c.post('/auth/login',json={'email':'none@example.test','password':'wrong-password'}).status_code==401
    assert c.post('/auth/login',json={'email':'none@example.test','password':'wrong-password'}).status_code==429
    with Session() as db:
        assert db.scalar(select(Rate.count))==11
    r=c.post('/auth/register',json={'email':'x@example.test','password':'test-password-123'})
    assert 'HttpOnly' in r.headers['set-cookie'] and 'SameSite=strict' in r.headers['set-cookie']

def test_revoke_cancels_approved_authorization():
    c=browser();i,p=begin(c);assert approve(c,p).status_code==200
    profile=c.get('/account/devices').json()[0]
    assert c.post('/account/devices/'+profile['id']+'/revoke').status_code==200
    assert c.post('/device/pairings/poll',json={'device_code':p['device_code']}).status_code==410

def test_concurrent_poll_issues_only_one_credential():
    from concurrent.futures import ThreadPoolExecutor
    c=browser();i,p=begin(c);assert approve(c,p).status_code==200
    def attempt(_):
        with TestClient(app) as another:
            return another.post('/device/pairings/poll',json={'device_code':p['device_code']})
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(attempt,range(2)))
    assert sorted(r.status_code for r in results)==[200,410]

def test_concurrent_same_batch_is_imported_once():
    from concurrent.futures import ThreadPoolExecutor
    c=browser();_,_,t=paired(c);data=sample()
    def attempt(_):
        with TestClient(app) as another:
            return upload(another,t['device_token'],data)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(attempt,range(2)))
    assert all(r.status_code==200 for r in results)
    assert sorted(r.json()['status'] for r in results)==['duplicate','imported']
    assert len(c.get('/account/library').json())==2

def test_artwork_requires_owned_real_trophy_and_authorizes_before_cache():
    from app.models import Artwork
    from test_artwork import image
    import hashlib
    c=browser();other=browser('other@example.test');_,_,t=paired(c)
    content=image();sha=hashlib.sha256(content).hexdigest()
    with Session() as db:
        db.add(Artwork(id='a'*64,source='ps5_native',title_id='MOCK001',trophy_id='0',digest=sha,content=content));db.commit()
    s=sample();assert upload(c,t['device_token'],s).status_code==200
    assert c.get('/account/artwork/'+'a'*64).status_code==404  # Mock ownership is insufficient.
    assert all(r['icon_url'] is None for r in c.get('/account/library').json())
    s['mock']=False;s['batch_id']=str(uuid.uuid4())
    assert upload(c,t['device_token'],s).status_code==200
    r=c.get('/account/artwork/'+'a'*64);assert r.status_code==200 and r.content==content
    assert r.headers['content-type']=='image/png' and r.headers['x-content-type-options']=='nosniff'
    assert r.headers['cache-control']=='private, no-cache' and r.headers['vary']=='Cookie'
    headers={'if-none-match':r.headers['etag']}
    assert c.get('/account/artwork/'+'a'*64,headers=headers).status_code==304
    assert other.get('/account/artwork/'+'a'*64,headers=headers).status_code==404
    assert TestClient(app).get('/account/artwork/'+'a'*64).status_code==401
    assert c.get('/account/artwork/'+'b'*64).status_code==404
    actual=[r for r in c.get('/account/library').json() if not r['mock'] and r['kind']=='trophy'][0]
    assert actual['icon_url']=='/api/account/artwork/'+'a'*64

def test_localized_library_preserves_observations_ownership_and_secret_redaction():
    from app.models import TrophyText,TrophyInfo,Record
    c=browser();other=browser('other@example.test');_,_,token=paired(c)
    s=sample();s['mock']=False;s['activities']=[]
    s['trophies'][0].update(name='MOCK original observation',unlocked=False)
    assert upload(c,token['device_token'],s).status_code==200
    with Session() as db:
        db.add(TrophyInfo(source='ps5_native',title_id='MOCK001',trophy_id='0',hidden=True,description='MOCK English description'))
        for language,title,name in [('en-US','MOCK English title','MOCK English secret'),('fr-FR','MOCK titre français','MOCK secret français'),('pt-BR','MOCK título brasileiro','MOCK segredo brasileiro')]:
            for trophy,label,detail in [('',title,''),('0',name,'MOCK '+language+' description')]:
                db.add(TrophyText(source='ps5_native',title_id='MOCK001',trophy_id=trophy,language=language,name=label,description=detail,is_default=language=='en-US'))
        db.commit()
    row=c.get('/account/library?language=fr-BE,en-US').json()[0]
    assert row['content_language']=='fr-FR' and row['data']['title']=='MOCK titre français'
    assert row['data']['name']=='Hidden trophy' and row['data']['description'] is None
    assert other.get('/account/library?language=fr-FR').json()==[]
    assert TestClient(app).get('/account/library?language=fr-FR').status_code==401
    assert c.get('/account/library',params={'language':'a'*161}).status_code==422
    s['batch_id']=str(uuid.uuid4());s['trophies'][0]['unlocked']=True
    assert upload(c,token['device_token'],s).status_code==200
    row=c.get('/account/library?language=fr-FR').json()[0]
    assert row['data']['name']=='MOCK secret français' and row['data']['description']=='MOCK fr-FR description'
    assert c.get('/account/library?language=pt-BR').json()[0]['data']['name']=='MOCK segredo brasileiro'
    assert c.get('/account/library?language=xx').json()[0]['data']['name']=='MOCK English secret'
    with Session() as db:
        assert db.scalar(select(Record)).data['name']=='MOCK original observation'

def native_activity(seconds=120,complete=True):
    return {'schema_version':3,'batch_id':str(uuid.uuid4()),'source':'ps5_native','mock':False,
        'consistency':'sqlite_read_transaction','profile_binding':'activity_header_single_local_user',
        'trophies':[],'activities':[{'event_id':'native-session:'+'a'*64,'title_id':'PPSA12345','title':'MOCK GAME',
         'started_at':'2026-10-08T10:00:00Z','ended_at':'2026-10-08T10:02:00Z' if complete else None,
         'duration_seconds':seconds if complete else None,'complete':complete,'clock':'uncertain',
         'duration_basis':'native_foreground_seconds','native_observation':{'application_title_id':'PPSA12345',
          'session_digest':'a'*64,'foreground_seconds':seconds if complete else None,
          'event':'ApplicationSessionEnd' if complete else 'ApplicationSessionStart'}}]}

def test_native_playtime_idempotency_monotonic_counter_and_owned_title_join():
    c=browser();other=browser('other@example.test');_,_,token=paired(c)
    trophy=sample();trophy['mock']=False;trophy['activities']=[]
    assert upload(c,token['device_token'],trophy).status_code==200
    body=native_activity()
    assert upload(c,token['device_token'],body).status_code==200
    assert upload(c,token['device_token'],body).json()['status']=='duplicate'
    for later in (native_activity(180),native_activity(60),native_activity(complete=False)):
        assert upload(c,token['device_token'],later).status_code==200
    rows=c.get('/account/library').json();activity=next(r['data'] for r in rows if r['kind']=='activity')
    assert len(rows)==2 and activity['duration_seconds']==180 and activity['complete']
    assert activity['clock']=='uncertain' and activity['duration_basis']=='native_foreground_seconds'
    assert activity['title_id']=='MOCK001' and activity['native_observation']['application_title_id']=='PPSA12345'
    assert activity['title_binding']=='unique_local_title_metadata'
    assert other.get('/account/library').json()==[]
    from app.models import Record
    with Session() as db:
        assert db.scalar(select(Record).where(Record.kind=='activity')).data['title_id']=='PPSA12345'

def test_native_playtime_requires_profile_binding_counter_and_session_evidence():
    c=browser();_,_,token=paired(c)
    for mutation in ('counter','identity','binding','event','mock','title'):
        s=native_activity();a=s['activities'][0]
        if mutation=='counter':a['duration_seconds']=121
        if mutation=='identity':a['native_observation']['session_digest']='b'*64
        if mutation=='binding':s['profile_binding']='foreground_user_path_scoped'
        if mutation=='event':a['native_observation']['event']='ApplicationSessionEndBi'
        if mutation=='mock':s['mock']=True
        if mutation=='title':a['title_id']='PPSA99999'
        assert upload(c,token['device_token'],s).status_code==422,mutation

def test_secret_trophies_are_redacted_until_earned_and_locked_icons_denied():
    from app.models import Artwork, TrophyInfo
    from test_artwork import image
    import hashlib
    c=browser();_,_,t=paired(c);s=sample();s['mock']=False;s['activities']=[]
    s['trophies'][0].update(name='SYNTHETIC secret name',unlocked=False)
    assert upload(c,t['device_token'],s).status_code==200
    content=image();sha=hashlib.sha256(content).hexdigest()
    with Session() as db:
        db.add(TrophyInfo(source='ps5_native',title_id='MOCK001',trophy_id='0',hidden=True,description='SYNTHETIC secret description'))
        db.add(Artwork(id='a'*64,source='ps5_native',title_id='MOCK001',trophy_id='0',digest=sha,content=content));db.commit()
    row=c.get('/account/library').json()[0]
    assert row['data']['name']=='Hidden trophy' and row['data']['description'] is None
    assert row['data']['hidden'] is True and row['icon_url'] is None
    assert c.get('/account/artwork/'+'a'*64,headers={'if-none-match':'"'+sha+'"'}).status_code==404
    s['batch_id']=str(uuid.uuid4());s['trophies'][0]['unlocked']=True
    assert upload(c,t['device_token'],s).status_code==200
    row=c.get('/account/library').json()[0]
    assert row['data']['name']=='SYNTHETIC secret name' and row['data']['description']=='SYNTHETIC secret description'
    assert row['icon_url'] is not None and c.get('/account/artwork/'+'a'*64).status_code==200


def test_artwork_incomplete_upload_never_changes_cache():
    from app.models import DevicePackage,DeviceArtwork
    c=browser();_,_,t=paired(c)
    response=c.post('/device/artwork',headers={'authorization':'Bearer '+t['device_token'],
                    'content-type':'application/octet-stream','content-length':'4096'},content=b'MOCK-partial')
    assert response.status_code==400
    assert response.json()['detail']=='Artwork upload incomplete; retry sync'
    with Session() as db:
        assert db.scalar(select(DevicePackage)) is None
        assert db.scalar(select(DeviceArtwork)) is None

def test_artwork_disconnect_is_handled_before_cache_changes():
    import asyncio
    from fastapi import HTTPException,Request
    from app.main import device_artwork
    from app.models import DevicePackage,DeviceArtwork
    c=browser();_,_,t=paired(c)
    messages=iter([{'type':'http.request','body':b'MOCK-partial','more_body':True},
                   {'type':'http.disconnect'}])
    async def receive():return next(messages)
    scope={'type':'http','method':'POST','path':'/device/artwork','headers':[
        (b'content-type',b'application/octet-stream'),(b'content-length',b'4096'),
        (b'authorization',('Bearer '+t['device_token']).encode())]}
    with Session() as db:
        profile=db.get(Profile,t['profile_uuid'])
        with pytest.raises(HTTPException) as failure:
            asyncio.run(device_artwork(Request(scope,receive),profile,db))
        assert failure.value.status_code==400
        assert failure.value.detail=='Artwork upload interrupted; retry sync'
        assert db.scalar(select(DevicePackage)) is None
        assert db.scalar(select(DeviceArtwork)) is None

def test_device_artwork_automatic_cache_is_private_localized_and_idempotent():
    import hashlib,json
    from test_artwork import package,image
    from app.models import DeviceArtwork,DevicePackage,Record
    c=browser();_,_,t=paired(c);headers={'authorization':'Bearer '+t['device_token']}
    outsider=browser('other-art@example.test');_,_,other=paired(outsider)
    conf={'schemaVersion':'1.00','platform':['PS5'],'trophyNpCommId':'NPWR12345_00',
        'defaultLanguage':'en-US','trophyDefinitionRevision':'1','trophySetVersion':'1',
        'trophies':[{'id':'0','hidden':True}]}
    def meta(label):
        return {**{k:conf[k] for k in ('trophyNpCommId','trophyDefinitionRevision','trophySetVersion')},
            'schemaVersion':'0.90','metadata':{'titleMetadata':{'name':'MOCK GAME'},
            'trophyMetadata':[{'id':'0','name':label,'detail':'MOCK description'}]}}
    raw=package({'tropconf.json':json.dumps(conf).encode(),
        'tropmeta_en-US.json':json.dumps(meta('MOCK EN')).encode(),
        'tropmeta_fr.json':json.dumps(meta('MOCK FR')).encode(),
        'trop0000.png':image(),'icon0_en-US.png':image()})
    sha=hashlib.sha256(raw).hexdigest();check={'title_id':'NPWR12345_00','sha256':sha}
    assert c.post('/device/artwork/check',headers=headers,json=check).status_code==403
    s=sample();s.update(mock=False,activities=[]);s['trophies'][0].update(title_id=conf['trophyNpCommId'],unlocked=False)
    assert upload(c,t['device_token'],s).status_code==200
    assert c.post('/device/artwork/check',headers=headers,json=check).json()=={'needed':True}
    binary={**headers,'content-type':'application/octet-stream'}
    assert c.post('/device/artwork',headers=binary,content=raw).status_code==200
    assert c.post('/device/artwork',headers=binary,content=raw).status_code==200
    assert c.post('/device/artwork/check',headers=headers,json=check).json()=={'needed':False}
    assert outsider.post('/device/artwork',headers={'authorization':'Bearer '+other['device_token'],'content-type':'application/octet-stream'},content=raw).status_code==403
    row=c.get('/account/library?language=fr').json()[0]
    assert row['data']['name']=='Hidden trophy' and row['data']['description'] is None and row['icon_url'] is None
    url=row['artwork_url'].replace('/api','',1)
    assert c.get(url).status_code==200 and outsider.get(url).status_code==404
    with Session() as db:
        assert len(list(db.scalars(select(DevicePackage))))==1
        icons=list(db.scalars(select(DeviceArtwork)));assert len(icons)==2
        locked=next(i for i in icons if i.trophy_id)
        locked_id=locked.id
    assert c.get('/account/device-artwork/'+locked_id).status_code==404
    s['batch_id']=str(uuid.uuid4());s['trophies'][0]['unlocked']=True
    assert upload(c,t['device_token'],s).status_code==200
    row=c.get('/account/library?language=fr').json()[0]
    assert row['data']['name']=='MOCK FR' and row['icon_url']
    assert c.get(row['icon_url'].replace('/api','',1)).status_code==200
    bad=raw[:-1];assert c.post('/device/artwork',headers=binary,content=bad).status_code==422
    assert c.post('/device/artwork',headers={'content-type':'application/octet-stream'},content=raw).status_code==401
    assert c.post('/device/artwork',headers=binary,content=b'x',).status_code==422
    c.post('/account/devices/'+t['profile_uuid']+'/revoke',json={})
    assert c.post('/device/artwork',headers=binary,content=raw).status_code==401

def test_library_hides_activity_only_titles_without_deleting_source_records():
    from app.models import Record
    c=browser();_,_,t=paired(c)
    assert upload(c,t['device_token'],native_activity()).status_code==200
    assert c.get('/account/library').json()==[]
    with Session() as db:assert db.scalar(select(Record).where(Record.kind=='activity')) is not None


def social_handle(client):
    r=client.get('/account/profile');assert r.status_code==200
    return r.json()['handle']


def test_public_profile_identity_and_explicit_friend_permissions():
    a,b,c=browser(),browser('b@example.test'),browser('c@example.test')
    ah,bh=social_handle(a),social_handle(b)
    public=TestClient(app).get('/players/'+bh)
    assert public.status_code==200
    assert set(public.json())=={'handle','display_name','relationship','viewer_authenticated','request_id','library_visible'}
    assert 'example.test' not in public.text and public.json()['request_id'] is None
    assert b.get('/players?q='+bh).json()[0]['handle']==bh
    assert a.post('/account/profile',json={'handle':bh,'display_name':'Collision'}).status_code==409
    assert a.post('/account/profile',json={'handle':'my_player','display_name':'My player'}).status_code==200
    assert a.post('/account/friends/request',json={'handle':'my_player'}).status_code==400
    link=a.post('/account/friends/request',json={'handle':bh}).json()['request_id']
    assert a.get('/account/friends/'+bh+'/compare').status_code==403
    assert b.post('/account/friends/request',json={'handle':'my_player'}).json()['relationship']=='incoming'
    assert a.post('/account/friends/'+link,json={'action':'accept'}).status_code==403
    assert c.post('/account/friends/'+link,json={'action':'accept'}).status_code==404
    assert b.post('/account/friends/'+link,json={'action':'cancel'}).status_code==403
    assert b.post('/account/friends/'+link,json={'action':'accept'}).status_code==200
    assert a.get('/account/friends/'+bh+'/compare').status_code==200
    assert a.get('/account/friends').json()['friends'][0]['handle']==bh
    assert b.post('/account/friends/'+link,json={'action':'remove'}).status_code==200
    assert a.get('/account/friends/'+bh+'/compare').status_code==403
    assert a.post('/account/friends/request',headers={'origin':'https://evil.test'},json={'handle':bh}).status_code==403


def test_denial_history_cooldown_and_sender_cancellation():
    a,b=browser(),browser('b@example.test');bh=social_handle(b)
    link=a.post('/account/friends/request',json={'handle':bh}).json()['request_id']
    assert b.post('/account/friends/'+link,json={'action':'deny'}).status_code==200
    assert a.get('/account/friends').json()['denied'][0]['handle']==bh
    assert b.get('/account/friends').json()['incoming']==[]
    assert a.post('/account/friends/request',json={'handle':bh}).status_code==429
    from app.models import Friendship
    with Session() as db:db.get(Friendship,link).updated=0;db.commit()
    assert a.post('/account/friends/request',json={'handle':bh}).json()['relationship']=='outgoing'
    assert a.post('/account/friends/'+link,json={'action':'cancel'}).status_code==200
    assert b.get('/account/friends').json()['incoming']==[]


def test_comparison_masks_friend_secrets_and_artwork_until_viewer_earns():
    from app.models import Record,Artwork,TrophyInfo
    a,b=browser(),browser('b@example.test');_,_,at=paired(a);_,_,bt=paired(b)
    bh=social_handle(b)
    # Synthetic non-mock database fixtures exercise serializers; no hardware claim.
    with Session() as db:
        for token,unlocked in [(at,False),(bt,True)]:
            db.add(Record(id=str(uuid.uuid4()),profile=token['profile_uuid'],source='ps5_native',kind='trophy',key='SET:0',mock=False,data={'title_id':'SET','title':'Test game','trophy_id':'0','name':'SECRET NAME','grade':'gold','unlocked':unlocked}))
        db.add(TrophyInfo(source='ps5_native',title_id='SET',trophy_id='0',hidden=True,description='SECRET DESCRIPTION'))
        db.add(Artwork(id='secret-image',source='ps5_native',title_id='SET',trophy_id='0',digest='abc',content=b'test-png'))
        db.add(Artwork(id='game-image',source='ps5_native',title_id='SET',trophy_id='',digest='def',content=b'test-png'))
        db.commit()
    link=a.post('/account/friends/request',json={'handle':bh}).json()['request_id']
    b.post('/account/friends/'+link,json={'action':'accept'})
    path='/account/friends/'+bh
    summary=a.get(path+'/compare').json()['games'][0]
    assert summary['mine_earned']==0 and summary['friend_earned']==1 and summary['trophies']==[]
    r=a.get(path+'/compare?title_id=SET')
    trophy=r.json()['games'][0]['trophies'][0]
    assert trophy['hidden'] is True and trophy['icon_url'] is None and trophy['description'] is None
    assert 'SECRET' not in r.text and at['profile_uuid'] not in r.text and bt['profile_uuid'] not in r.text
    assert a.get(path+'/artwork/secret-image').status_code==404
    assert a.get(path+'/artwork/game-image').status_code==200
    with Session() as db:
        row=db.scalar(select(Record).where(Record.profile==at['profile_uuid']));row.data={**row.data,'unlocked':True};db.commit()
    r=a.get(path+'/compare?title_id=SET');assert r.json()['games'][0]['trophies'][0]['name']=='SECRET NAME'
    assert a.get(path+'/artwork/secret-image').status_code==200
    a.post('/account/friends/'+link,json={'action':'remove'})
    assert a.get(path+'/artwork/game-image').status_code==403


def test_comparison_union_preserves_platform_missing_and_unknown_states():
    from app.models import Record
    a,b=browser(),browser('b@example.test');_,_,at=paired(a);_,_,bt=paired(b);bh=social_handle(b)
    with Session() as db:
        for token,source,trophy,state in [(at,'ps5_native','0',None),(bt,'ps5_native','1',True),(bt,'ps4_bc','0',True)]:
            db.add(Record(id=str(uuid.uuid4()),profile=token['profile_uuid'],source=source,kind='trophy',key='SET:'+trophy,mock=False,data={'title_id':'SET','title':'Test game','trophy_id':trophy,'name':'Name','grade':'bronze','unlocked':state}))
        db.commit()
    link=a.post('/account/friends/request',json={'handle':bh}).json()['request_id'];b.post('/account/friends/'+link,json={'action':'accept'})
    games=a.get('/account/friends/'+bh+'/compare?title_id=SET').json()['games'];assert len(games)==2
    game=next(g for g in games if g['source']=='ps5_native');assert game['total']==2
    first=game['trophies'][0];assert first['mine'] is None and first['mine_present'] is True and first['friend_present'] is False
    second=game['trophies'][1];assert second['mine_present'] is False and second['friend'] is True and second['hidden'] is True


def test_public_library_masks_secrets_redacts_sources_and_excludes_revocation():
    from app.models import Record,Artwork,TrophyInfo
    owner,viewer=browser(),browser('viewer@example.test');_,_,token=paired(owner);_,_,other=paired(viewer)
    handle=social_handle(owner);anon=TestClient(app)
    assert anon.get('/players/'+handle+'/library').status_code==403
    assert owner.post('/account/profile',json={'handle':handle,'display_name':'Public player','visibility':'public'}).status_code==200
    with Session() as db:
        db.add(Record(id=str(uuid.uuid4()),profile=token['profile_uuid'],source='ps5_native',kind='trophy',key='SET:0',mock=False,data={'title_id':'SET','title':'Public game','trophy_id':'0','name':'SECRET NAME','grade':'gold','unlocked':True,'native_observation':{'raw_flags':17}}))
        db.add(Record(id=str(uuid.uuid4()),profile=token['profile_uuid'],source='ps5_native',kind='activity',key='SET:SESSION',mock=False,data={'title_id':'SET','title':'Public game','event_id':'PRIVATE_SESSION','complete':True,'duration_seconds':108,'clock':'trusted','started_at':'2026-10-08T10:00:00Z'}))
        db.add(TrophyInfo(source='ps5_native',title_id='SET',trophy_id='0',hidden=True,description='SECRET DESCRIPTION'))
        db.add(Artwork(id='secret-image',source='ps5_native',title_id='SET',trophy_id='0',digest='abc',content=b'png'))
        db.add(Artwork(id='game-image',source='ps5_native',title_id='SET',trophy_id='',digest='def',content=b'png'))
        db.commit()
    path='/players/'+handle
    assert anon.get(path).json()['library_visible'] is True
    response=anon.get(path+'/library');assert response.status_code==200
    assert 'SECRET' not in response.text and 'PRIVATE_SESSION' not in response.text and 'native_observation' not in response.text and token['profile_uuid'] not in response.text
    rows=response.json();assert rows[0]['data']['unlocked'] is True and rows[0]['data']['concealed'] is True
    total=next(r for r in rows if r['kind']=='activity');assert total['data']['duration_seconds']==108 and total['data']['duration_basis']=='shared_total'
    assert anon.get(path+'/artwork/secret-image').status_code==404
    assert anon.get(path+'/artwork/game-image').status_code==200
    with Session() as db:
        db.add(Record(id=str(uuid.uuid4()),profile=other['profile_uuid'],source='ps5_native',kind='trophy',key='SET:0',mock=False,data={'title_id':'SET','title':'Public game','trophy_id':'0','name':'SECRET NAME','grade':'gold','unlocked':True}));db.commit()
    assert viewer.get(path+'/library').json()[0]['data']['name']=='SECRET NAME'
    assert viewer.get(path+'/artwork/secret-image').status_code==200
    owner.post('/account/profile',json={'handle':handle,'display_name':'Public player','visibility':'friends'})
    assert anon.get(path+'/library').status_code==403 and anon.get(path+'/artwork/game-image').status_code==403
    link=viewer.post('/account/friends/request',json={'handle':handle}).json()['request_id'];owner.post('/account/friends/'+link,json={'action':'accept'})
    assert viewer.get(path+'/library').status_code==200
    owner.post('/account/devices/'+token['profile_uuid']+'/revoke',json={})
    assert owner.get('/account/devices').json()==[] and owner.get('/account/library').json()==[]
    assert viewer.get(path+'/library').json()==[] and viewer.get(path+'/artwork/game-image').status_code==404


def test_normal_runtime_rejects_and_filters_demo_imports(monkeypatch):
    import app.main as main
    c=browser();_,_,token=paired(c)
    assert upload(c,token['device_token'],sample()).status_code==200
    monkeypatch.setattr(main,'development_tools',False)
    assert c.get('/account/library').json()==[]
    assert upload(c,token['device_token'],sample()).status_code==422
