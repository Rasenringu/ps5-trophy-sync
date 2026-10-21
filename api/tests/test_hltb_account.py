"""Synthetic connector identity and receipts, never a live-account validation."""
import copy
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from app.main import app,digest,now
from app.db import Session
from app.models import HltbPairing,HltbConnection,HltbPublication,Record
from app import howlongtobeat
from test_flow import reset,browser
from test_insights import seed,KEY
from test_hltb import GAME

PREFIX='/account/integrations/howlongtobeat'
BRIDGE='/integrations/howlongtobeat'
PUBLISH='/account/games/howlongtobeat/publish'
BODY={**KEY,'hltb_id':123,'seconds':3500,'confirm':True}

@pytest.fixture(autouse=True)
def provider(monkeypatch):
    monkeypatch.setenv('HLTB_ENABLED','true')
    monkeypatch.setattr(howlongtobeat,'fetch',lambda *args:{'games':[copy.deepcopy(GAME)]})

def connect(owner,user_id=1234):
    code=owner.post(PREFIX+'/connect',json={}).json()['code']
    bridge=TestClient(app)
    result=bridge.post(BRIDGE+'/claim',json={'code':code,'user_id':user_id,'username':'SYNTHETIC'})
    assert result.status_code==200,result.text
    bridge.headers['Authorization']='Bearer '+result.json()['token']
    return bridge,code,result.json()['token']

def playtime(owner,**changes):
    token=seed(owner)
    with Session() as db:
        db.add(Record(id=str(uuid.uuid4()),profile=token['profile_uuid'],source='ps5_native',kind='activity',
            key='SYNTHETIC_SESSION',mock=False,data={'title_id':KEY['title_id'],'title':'SYNTHETIC Game',
                'event_id':'SYNTHETIC_SESSION','duration_seconds':3500,'complete':True,'clock':'trusted',**changes}))
        db.commit()
    return token

def test_pairing_is_single_use_expiring_and_both_tokens_are_hashed():
    owner=browser();bridge,code,token=connect(owner)
    assert bridge.post(BRIDGE+'/claim',json={'code':code,'user_id':1234,'username':'SYNTHETIC'}).status_code==401
    with Session() as db:
        row=db.scalar(select(HltbConnection));assert row.token==digest(token) and token not in row.token
        assert db.scalar(select(HltbPairing)) is None
    pending=owner.post(PREFIX+'/connect',json={}).json()
    with Session() as db:
        row=db.scalar(select(HltbPairing));assert row.code==digest(pending['code']);row.expires=0;db.commit()
    assert bridge.post(BRIDGE+'/claim',json={'code':pending['code'],'user_id':1234,'username':'SYNTHETIC'}).status_code==401

def test_reviewed_publication_is_idempotent_and_receipt_requires_exact_readback():
    owner=browser();playtime(owner);bridge,_,_=connect(owner)
    first=owner.post(PUBLISH,json=BODY);assert first.status_code==200,first.text
    job=first.json();assert owner.post(PUBLISH,json=BODY).json()['id']==job['id']
    next_=bridge.post(BRIDGE+'/next',json={}).json()
    assert next_['job']['id']==job['id'] and next_['reconcile_only'] is False
    assert bridge.post(BRIDGE+'/next',json={}).json()['job'] is None
    receipt={'job_id':job['id'],'state':'synced','submission_id':9876,'seconds':3500}
    assert bridge.post(BRIDGE+'/receipt',json={**receipt,'seconds':3501}).status_code==422
    assert bridge.post(BRIDGE+'/receipt',json=receipt).json()['state']=='synced'
    assert owner.post(PUBLISH,json=BODY).json()['state']=='synced'
    assert bridge.post(BRIDGE+'/receipt',json=receipt).status_code==200
    status=owner.get(PREFIX+'/connection');assert status.json()['username']=='SYNTHETIC'
    assert 'token' not in status.text and 'cookie' not in status.text
    with Session() as db:assert db.query(HltbPublication).count()==1

def test_ownership_csrf_and_connector_scope():
    owner=browser();playtime(owner);other=browser('other@example.test');bridge,_,_=connect(owner)
    assert other.post(PUBLISH,json=BODY).status_code==404
    assert TestClient(app).get(PREFIX+'/connection').status_code==401
    assert bridge.get('/account/library').status_code==401
    assert bridge.post(PUBLISH,json=BODY).status_code==403
    job=owner.post(PUBLISH,json=BODY).json()
    other_bridge,_,_=connect(other,4321)
    assert other_bridge.post(BRIDGE+'/receipt',json={'job_id':job['id'],'state':'failed','error':'invalid_response'}).status_code==404
    owner.headers['origin']='https://evil.invalid'
    assert owner.post(PREFIX+'/disconnect',json={}).status_code==403

@pytest.mark.parametrize('changes',[{'seconds':3501},{'hltb_id':999},{'confirm':False},{'confirm':1}])
def test_changed_time_wrong_listing_or_missing_explicit_review_cannot_publish(changes):
    owner=browser();playtime(owner);connect(owner)
    assert owner.post(PUBLISH,json={**BODY,**changes}).status_code in (409,422)

def test_uncertain_and_interrupted_jobs_are_read_only_reconciliation():
    owner=browser();playtime(owner);bridge,_,_=connect(owner)
    job=owner.post(PUBLISH,json=BODY).json();bridge.post(BRIDGE+'/next',json={})
    with Session() as db:db.get(HltbPublication,job['id']).updated=now()-121;db.commit()
    assert bridge.post(BRIDGE+'/next',json={}).json()['reconcile_only'] is True
    assert bridge.post(BRIDGE+'/receipt',json={'job_id':job['id'],'state':'uncertain','error':'write_unverified'}).status_code==200
    assert bridge.post(BRIDGE+'/next',json={}).json()['reconcile_only'] is True

def test_revocation_and_relink_rotate_token_cancel_pending_and_enforce_provider_identity():
    owner=browser();playtime(owner);bridge,_,_=connect(owner)
    job=owner.post(PUBLISH,json=BODY).json()
    newer,_,_=connect(owner,5678)
    assert bridge.post(BRIDGE+'/next',json={}).status_code==401
    assert newer.post(BRIDGE+'/next',json={}).json()['job'] is None
    assert owner.get(PREFIX+'/connection').json()['publications'][0]['state']=='cancelled'
    assert owner.post(PREFIX+'/disconnect',json={}).status_code==200
    assert newer.post(BRIDGE+'/next',json={}).status_code==401
    assert owner.post(PUBLISH,json=BODY).status_code==409

def test_hiding_or_profile_revocation_cancels_unexecuted_jobs():
    owner=browser();token=playtime(owner);bridge,_,_=connect(owner)
    owner.post(PUBLISH,json=BODY)
    owner.post('/account/games/visibility',json={**KEY,'hidden':True})
    assert bridge.post(BRIDGE+'/next',json={}).json()['job'] is None
    assert owner.post(PUBLISH,json=BODY).status_code==422
    owner.post('/account/devices/'+token['profile_uuid']+'/revoke',json={})
    assert owner.post(PUBLISH,json=BODY).status_code==404

def test_incomplete_playtime_cannot_be_uploaded_as_zero_or_assumed_complete():
    owner=browser();playtime(owner,complete=False);connect(owner)
    assert owner.post(PUBLISH,json=BODY).status_code==409

def test_relinking_after_interrupted_write_cannot_reset_uncertainty():
    owner=browser();playtime(owner);bridge,_,_=connect(owner)
    owner.post(PUBLISH,json=BODY);bridge.post(BRIDGE+'/next',json={})
    replacement,_,_=connect(owner)
    assert owner.post(PUBLISH,json=BODY).json()['state']=='pending'
    assert replacement.post(BRIDGE+'/next',json={}).json()['reconcile_only'] is True
