"""Synthetic native activity + PNG fixtures; no console or hosted data access."""
import hashlib
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import select
from app.db import Session
from app.main import app
from app.models import DeviceArtwork
from test_flow import browser, paired, upload, native_activity, social_handle, reset
from test_artwork import image

def test_application_artwork_requires_owned_real_activity_and_reuses_private_cache():
    owner=browser();_,_,device=paired(owner)
    other=browser('outside@example.test');_,_,foreign=paired(other)
    png=image();sha=hashlib.sha256(png).hexdigest()
    check={'title_id':'PPSA12345','sha256':sha}
    headers={'authorization':'Bearer '+device['device_token']}
    binary={**headers,'content-type':'application/octet-stream'}
    path='/device/application-artwork/PPSA12345'
    assert owner.post('/device/application-artwork/check',headers=headers,json=check).status_code==403
    assert owner.post(path,headers=binary,content=png).status_code==403
    assert upload(owner,device['device_token'],native_activity()).status_code==200
    assert owner.post('/device/application-artwork/check',headers=headers,json=check).json()=={'needed':True}
    for _ in range(2):
        assert owner.post(path,headers=binary,content=png).json()=={'status':'stored','title_id':'PPSA12345','sha256':sha}
    assert owner.post('/device/application-artwork/check',headers=headers,json=check).json()=={'needed':False}
    row=owner.get('/account/library').json()[0]
    assert row['kind']=='activity' and row['icon_url'] is None and row['artwork_url']
    url=row['artwork_url'].replace('/api','',1)
    response=owner.get(url);assert response.status_code==200 and response.content==png
    assert owner.get(url,headers={'if-none-match':response.headers['etag']}).status_code==304
    assert other.get(url,headers={'if-none-match':response.headers['etag']}).status_code==404
    assert TestClient(app).get(url).status_code==401
    assert other.post(path,headers={'authorization':'Bearer '+foreign['device_token'],'content-type':'application/octet-stream'},content=png).status_code==403
    assert owner.post(path,headers=binary,content=png[:-1]).status_code==422
    assert owner.post(path,headers=binary,content=b'x'*2_000_001).status_code==413
    assert owner.post('/device/application-artwork/NPWR12345_00',headers=binary,content=png).status_code==422
    with Session() as db:assert len(list(db.scalars(select(DeviceArtwork))))==1
    owner.post('/account/devices/'+device['profile_uuid']+'/revoke',json={})
    assert owner.get(url).status_code==404
    assert owner.post(path,headers=binary,content=png).status_code==401

def test_ps4_application_artwork_is_shared_only_with_library_access_and_without_sessions():
    owner=browser();_,_,device=paired(owner)
    body=native_activity();row=body['activities'][0]
    row.update(title_id='CUSA03804',title='MOCK Attack on Titan')
    row['native_observation']['application_title_id']='CUSA03804'
    assert upload(owner,device['device_token'],body).status_code==200
    assert owner.post('/device/application-artwork/CUSA03804',headers={
        'authorization':'Bearer '+device['device_token'],'content-type':'application/octet-stream'},content=image()).status_code==200
    handle=social_handle(owner);anon=TestClient(app)
    owner.post('/account/profile',json={'handle':handle,'display_name':'MOCK player','visibility':'public'})
    rows=anon.get('/players/'+handle+'/library').json()
    assert len(rows)==1 and rows[0]['kind']=='activity' and rows[0]['artwork_url']
    assert 'native_observation' not in rows[0]['data'] and 'started_at' not in rows[0]['data']
    url=rows[0]['artwork_url'].replace('/api','',1)
    assert anon.get(url).status_code==200
    owner.post('/account/profile',json={'handle':handle,'display_name':'MOCK player','visibility':'friends'})
    assert anon.get(url).status_code==403

def test_ps4_playtime_does_not_alias_a_same_named_native_ps5_trophy_set():
    from test_flow import sample
    owner=browser();_,_,device=paired(owner)
    trophy=sample();trophy.update(mock=False,activities=[])
    assert upload(owner,device['device_token'],trophy).status_code==200
    body=native_activity();row=body['activities'][0]
    row.update(title_id='CUSA03804')
    row['native_observation']['application_title_id']='CUSA03804'
    assert upload(owner,device['device_token'],body).status_code==200
    rows=owner.get('/account/library').json()
    assert next(row for row in rows if row['kind']=='activity')['data']['title_id']=='CUSA03804'
