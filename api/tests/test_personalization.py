"""Synthetic ownership/privacy fixtures; no console validation claim."""
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.db import Session
from app.models import Record, Artwork, HiddenGame
from test_flow import reset, browser, paired, social_handle, native_activity, upload, sample

def seed(client):
    _,_,token=paired(client,local=uuid.uuid4().hex)
    with Session() as db:
        for source in ('ps5_native','ps4_bc'):
            db.add(Record(id=str(uuid.uuid4()),profile=token['profile_uuid'],source=source,kind='trophy',key='SET:0',mock=False,
                data={'title_id':'SET','title':'Fixture '+source,'trophy_id':'0','name':'Normal trophy','hidden':False,'grade':'gold','unlocked':True}))
        db.add(Record(id=str(uuid.uuid4()),profile=token['profile_uuid'],source='ps5_native',kind='activity',key='recent',mock=False,
            data={'title_id':'SET','title':'Fixture ps5_native','complete':False,'duration_seconds':None,'started_at':'2026-10-14T10:00:00Z','clock':'uncertain'}))
        if not db.get(Artwork,'fixture-game'):
            db.add(Artwork(id='fixture-game',source='ps5_native',title_id='SET',trophy_id='',digest='abc',content=b'png'))
            db.add(Artwork(id='fixture-trophy',source='ps5_native',title_id='SET',trophy_id='0',digest='def',content=b'png'))
        db.commit()
    return token

def edit(client,**changes):
    return client.post('/account/profile',json={'handle':social_handle(client),'display_name':'Fixture player',**changes})

def test_hidden_games_excluded_from_all_shared_routes_and_survive_observations():
    owner,friend=browser(),browser('friend@example.test');token=seed(owner);seed(friend)
    handle=social_handle(owner);edit(owner,visibility='public',favorite={'source':'ps5_native','title_id':'SET'})
    link=friend.post('/account/friends/request',json={'handle':handle}).json()['request_id']
    owner.post('/account/friends/'+link,json={'action':'accept'})
    anon=TestClient(app);path='/players/'+handle
    assert anon.get(path).json()['favorite']['title']=='Fixture ps5_native'
    response=anon.get(path+'/library')
    activity=next(r['data'] for r in response.json() if r['kind']=='activity')
    assert activity['last_played_at']=='2026-10-14T10:00:00Z' and activity['duration_seconds'] is None
    assert 'started_at' not in response.text and token['profile_uuid'] not in response.text
    assert anon.get(path+'/artwork/fixture-game').status_code==200
    hide={'source':'ps5_native','title_id':'SET','hidden':True}
    for _ in range(2):assert owner.post('/account/games/visibility',json=hide).status_code==200
    assert anon.get(path).json()['favorite'] is None
    assert all(r['source']=='ps4_bc' for r in anon.get(path+'/library').json())
    assert all(g['source']=='ps4_bc' for g in friend.get('/account/friends/'+handle+'/compare').json()['games'])
    for image in ('fixture-game','fixture-trophy'):
        assert anon.get(path+'/artwork/'+image,headers={'if-none-match':'"abc"'}).status_code==404
        assert friend.get('/account/friends/'+handle+'/artwork/'+image).status_code==404
    rows=owner.get('/account/library').json()
    assert len(rows)==3 and all(r['game_hidden']==(r['source']=='ps5_native') for r in rows)
    # Reader updates are orthogonal to the visibility preference.
    with Session() as db:
        record=db.query(Record).filter(Record.profile==token['profile_uuid'],Record.kind=='activity').one()
        record.data={**record.data,'started_at':'2026-10-14T11:00:00Z'};db.commit()
        assert db.get(HiddenGame,(db.query(HiddenGame).one().account,'ps5_native','SET')) is not None
    assert all(r['source']=='ps4_bc' for r in anon.get(path+'/library').json())
    for _ in range(2):assert owner.post('/account/games/visibility',json={**hide,'hidden':False}).status_code==200
    assert len(anon.get(path+'/library').json())==3
    assert anon.get(path).json()['favorite'] is not None
    assert owner.get('/account/hidden-games').json()==[]

def test_visibility_is_owned_account_scoped_and_platform_specific():
    owner,other=browser(),browser('other@example.test');seed(owner)
    key={'source':'ps5_native','title_id':'SET','hidden':True}
    assert TestClient(app,headers={'origin':'http://localhost:3000'}).post('/account/games/visibility',json=key).status_code==401
    assert other.post('/account/games/visibility',json=key).status_code==404
    assert owner.post('/account/games/visibility',json=key).status_code==200
    # Same canonical game on a second console profile is hidden, without affecting PS4.
    seed(owner)
    rows=owner.get('/account/library').json()
    assert len({r['profile_uuid'] for r in rows})==2
    assert all(r['game_hidden']==(r['source']=='ps5_native') for r in rows)
    assert other.get('/account/hidden-games').json()==[]

def test_customization_validation_legacy_edits_and_private_showcase():
    owner=browser();token=seed(owner)
    assert edit(owner,bio='A little about me\nNext platinum: unknown',theme='violet',avatar='orbit',favorite={'source':'ps5_native','title_id':'SET'}).status_code==200
    profile=owner.get('/account/profile').json();handle=profile['handle']
    assert profile['theme']=='violet' and profile['avatar']=='orbit'
    assert edit(owner).json()['bio']==profile['bio']
    other=browser('collision@example.test')
    assert owner.post('/account/profile',json={'handle':social_handle(other),'display_name':'Collision','favorite':{'source':'ps5_native','title_id':'SET'}}).status_code==409
    anon=TestClient(app)
    assert anon.get('/players/'+handle).json()['favorite'] is None
    assert owner.get('/players/'+handle).json()['favorite']['title']=='Fixture ps5_native'
    for change in ({'bio':'x'*601},{'bio':'control\x00'},{'theme':'external-url'},{'avatar':'unknown'},{'favorite':{'source':'ps5_native','title_id':'NOT_OWNED'}}):
        assert edit(owner,**change).status_code==422
    owner.post('/account/games/visibility',json={'source':'ps5_native','title_id':'SET','hidden':True})
    assert edit(owner,favorite={'source':'ps5_native','title_id':'SET'}).status_code==422
    assert edit(owner,favorite=None).json()['favorite'] is None
    owner.post('/account/devices/'+token['profile_uuid']+'/revoke',json={})
    assert owner.get('/players/'+handle).json()['favorite'] is None

def test_hidden_application_stays_hidden_when_verified_trophy_join_arrives():
    owner=browser();_,_,token=paired(owner);handle=social_handle(owner)
    edit(owner,visibility='public')
    assert upload(owner,token['device_token'],native_activity()).status_code==200
    assert owner.post('/account/games/visibility',json={'source':'ps5_native','title_id':'PPSA12345','hidden':True}).status_code==200
    trophy=sample();trophy.update(mock=False,activities=[])
    assert upload(owner,token['device_token'],trophy).status_code==200
    anon=TestClient(app)
    # Application name evidence joins the activity to MOCK001. Preferences survive.
    rows=owner.get('/account/library').json()
    assert any(r['data']['title_id']=='MOCK001' and r['game_hidden'] for r in rows)
    assert all(r['game_hidden'] for r in rows)
    assert anon.get('/players/'+handle+'/library').json()==[]
    assert owner.post('/account/games/visibility',json={'source':'ps5_native','title_id':'MOCK001','hidden':False}).status_code==200
    assert len(anon.get('/players/'+handle+'/library').json())==2
