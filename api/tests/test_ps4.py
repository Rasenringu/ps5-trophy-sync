"""MOCK fixtures exercising PS4 ownership/proof, parsing, privacy and replay."""
import copy
import hashlib
import struct
from uuid import uuid4
import pytest
from Cryptodome.Cipher import AES
from fastapi.testclient import TestClient
from app.main import app
from app.ps4_artwork import _FORMAT_KEY,read_package
from test_flow import browser,paired,upload,native_activity,social_handle,reset
from test_artwork import image

def package(title='NPWR00001_00',xml=None):
    xml=xml or f'''<?xml version="1.0" encoding="UTF-8"?><trophyconf><npcommid>{title}</npcommid><title-name>MOCK PS4 game</title-name>
    <trophy id="000" hidden="no" ttype="B"><name>MOCK visible trophy</name><detail>MOCK detail</detail></trophy>
    <trophy id="001" hidden="yes" ttype="B"><name>MOCK secret trophy</name><detail>MOCK private description</detail></trophy></trophyconf>'''
    encoded=xml.encode();padding=16-len(encoded)%16;encoded+=bytes([padding])*padding
    key=AES.new(_FORMAT_KEY,AES.MODE_CBC,bytes(16)).encrypt(title.encode().ljust(16,b'\0'));iv=b'MOCK IV bytes!!!'
    encrypted=iv+AES.new(key,AES.MODE_CBC,iv).encrypt(encoded)
    entries={'TROP.ESFM':encrypted,'TROP_01.ESFM':encrypted,'ICON0.PNG':image(),'TROP000.PNG':image(),'TROP001.PNG':image()}
    blob=bytearray(96+64*len(entries));offset=len(blob)
    for i,(name,data) in enumerate(entries.items()):
        at=96+i*64;blob[at:at+32]=name.encode().ljust(32,b'\0');struct.pack_into('>QQ',blob,at+32,offset,len(data));blob+=data;offset+=len(data)
    struct.pack_into('>IIQII',blob,0,0xdca24d00,3,len(blob),len(entries),64);blob[28:48]=hashlib.sha1(blob).digest();return bytes(blob)

def snapshot(raw,title='NPWR00001_00',application='CUSA00001'):
    trophies=[]
    for identity in range(2):
        trophies.append({'title_id':title,'title':title,'trophy_id':str(identity),'name':'MOCK placeholder',
            'grade':'bronze','unlocked':identity==1,'unlocked_at':None,'clock':'unknown',
            'ps4_observation':{'raw_state':int(identity==1),'raw_aux':0x2000 if identity else 0,'raw_grade':4,
            'first_raw':'0','second_raw':'0','trp_sha1':raw[28:48].hex(),'application_title_ids':[application]}})
    return {'schema_version':4,'batch_id':str(uuid4()),'source':'ps4_bc','mock':False,'activities':[],'trophies':trophies,
        'consistency':'stable_encrypted_image_copy','profile_binding':'inner_local_user_and_foreground_path'}

def test_ps4_parser_integrity_identity_duplicate_names_and_xml_entities():
    raw=package();metadata,images=read_package(raw,'NPWR00001_00')
    assert metadata['format']=='ps4_trp_v3' and metadata['grades']=={'0':'bronze','1':'bronze'}
    assert metadata['info']['1'][0] is True and set(images)=={'','0','1'}
    with pytest.raises(ValueError):read_package(raw[:-1],'NPWR00001_00')
    with pytest.raises((ValueError,UnicodeError)):read_package(raw,'NPWR00002_00')
    with pytest.raises(ValueError):read_package(package(xml='<!DOCTYPE trophyconf [<!ENTITY x "mock">]><trophyconf/>'),'NPWR00001_00')
    duplicate=bytearray(raw);duplicate[160:192]=duplicate[96:128];duplicate[28:48]=bytes(20);duplicate[28:48]=hashlib.sha1(duplicate).digest()
    with pytest.raises(ValueError):read_package(bytes(duplicate),'NPWR00001_00')
    with pytest.raises(ValueError):read_package(package(xml='<trophyconf><npcommid>NPWR00001_00</npcommid><npcommid>NPWR00002_00</npcommid><title-name>MOCK</title-name></trophyconf>'),'NPWR00001_00')

def test_ps4_sync_artwork_cache_profile_access_and_secret_visibility():
    owner=browser();_,_,device=paired(owner);other=browser('outside-ps4@example.test');_,_,foreign=paired(other)
    raw=package();sha=hashlib.sha256(raw).hexdigest();headers={'authorization':'Bearer '+device['device_token']};binary={**headers,'content-type':'application/octet-stream'}
    check={'title_id':'NPWR00001_00','sha256':sha};path='/device/ps4-artwork/NPWR00001_00'
    assert owner.post('/device/ps4-artwork/check',headers=headers,json=check).status_code==403
    assert owner.post(path,headers=binary,content=raw).status_code==403
    body=snapshot(raw);assert upload(owner,device['device_token'],body).status_code==200
    assert upload(owner,device['device_token'],body).json()['status']=='duplicate'
    assert owner.post('/device/ps4-artwork/check',headers=headers,json=check).json()=={'needed':True}
    for _ in range(2):assert owner.post(path,headers=binary,content=raw).json()=={'status':'stored','title_id':'NPWR00001_00','sha256':sha}
    assert owner.post('/device/ps4-artwork/check',headers=headers,json=check).json()=={'needed':False}
    rows=owner.get('/account/library').json();assert len(rows)==2 and all(r['source']=='ps4_bc' and r['data']['title']=='MOCK PS4 game' for r in rows)
    assert rows[1]['data']['name']=='MOCK secret trophy' and rows[1]['icon_url']
    url=rows[1]['icon_url'].replace('/api','',1);response=owner.get(url);assert response.status_code==200
    assert other.get(url,headers={'if-none-match':response.headers['etag']}).status_code==404
    assert owner.get(url,headers={'if-none-match':response.headers['etag']}).status_code==304
    assert other.post(path,headers={'authorization':'Bearer '+foreign['device_token'],'content-type':'application/octet-stream'},content=raw).status_code==403
    assert owner.post(path,headers=binary,content=raw[:-1]).status_code==422
    assert owner.post(path,headers=binary,content=b'x'*(32*1024*1024+1)).status_code==413
    # Update as an unknown observation; previous earned state is retained.
    unknown=copy.deepcopy(body);unknown['batch_id']=str(uuid4());unknown['trophies'][1].update(unlocked=None)
    unknown['trophies'][1]['ps4_observation']['raw_state']=0x80000001
    assert upload(owner,device['device_token'],unknown).status_code==200
    assert owner.get('/account/library').json()[1]['data']['unlocked'] is True
    handle=social_handle(owner);owner.post('/account/profile',json={'handle':handle,'display_name':'MOCK PS4 player','visibility':'public'})
    shared=TestClient(app).get('/players/'+handle+'/library').json();assert len(shared)==2
    hidden=next(r for r in shared if r['data']['trophy_id']=='1');assert hidden['data']['name']=='Hidden trophy' and hidden['icon_url'] is None
    assert TestClient(app).get('/players/'+handle+'/artwork/'+url.rsplit('/',1)[1]).status_code==404
    owner.post('/account/devices/'+device['profile_uuid']+'/revoke',json={});assert owner.get(url).status_code==404
    assert owner.post(path,headers=binary,content=raw).status_code==401

def test_ps4_proof_validator_and_unique_activity_binding_no_double_count():
    owner=browser();_,_,device=paired(owner);raw=package();body=snapshot(raw)
    bad=copy.deepcopy(body);bad['trophies'][0]['unlocked']=True;assert upload(owner,device['device_token'],bad).status_code==422
    bad=copy.deepcopy(body);bad['trophies'][0]['grade']='gold';assert upload(owner,device['device_token'],bad).status_code==422
    bad=copy.deepcopy(body);bad['trophies'][0]['ps4_observation']['application_title_ids']=['PPSA00001'];assert upload(owner,device['device_token'],bad).status_code==422
    assert upload(owner,device['device_token'],body).status_code==200
    activity=native_activity();row=activity['activities'][0];row.update(title_id='CUSA00001',title='MOCK independently named PS4 app');row['native_observation']['application_title_id']='CUSA00001'
    assert upload(owner,device['device_token'],activity).status_code==200
    rows=owner.get('/account/library').json();session=next(r for r in rows if r['kind']=='activity')
    assert session['source']=='ps4_bc' and session['data']['title_id']=='NPWR00001_00' and session['data']['activity_source']=='ps5_native'
    before=session['data']['duration_seconds'];assert upload(owner,device['device_token'],activity).status_code==200
    assert next(r for r in owner.get('/account/library').json() if r['kind']=='activity')['data']['duration_seconds']==before
    # Two source sets claiming the application remain separate; never duplicate a session.
    assert upload(owner,device['device_token'],snapshot(package('NPWR00002_00'),'NPWR00002_00')).status_code==200
    sessions=[r for r in owner.get('/account/library').json() if r['kind']=='activity']
    assert len(sessions)==1 and sessions[0]['data']['title_id']=='CUSA00001' and sessions[0]['data']['duration_seconds']==before
