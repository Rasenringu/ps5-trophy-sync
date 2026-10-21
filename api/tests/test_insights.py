"""Synthetic integration contracts; no live HLTB/PlatPrices or console claims."""
import copy
import uuid
import httpx
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db import Session
from app.models import Record, TrophyText, TrophyInfo, GameInsight, ProviderCache
from app import platprices
from test_flow import reset, browser, paired, social_handle

KEY={'source':'ps5_native','title_id':'NPWR12345_00'}
PATH='/account/games/insights?source=ps5_native&title_id=NPWR12345_00'
GAME={'PPID':123,'GameName':'SYNTHETIC Game','IsPS5':1}
TROPHIES={'ppid':123,'total':2,'trophies':[
    {'id':700,'name':'First step','grade':'bronze','earned_rate':'0.0'},
    {'id':900,'name':'Secret ending','grade':'gold','earned_rate':None}]}
REAL_REQUEST=platprices.request_json

@pytest.fixture(autouse=True)
def fake_provider(monkeypatch):
    monkeypatch.setenv('PLATPRICES_API_KEY','SYNTHETIC_PROVIDER_KEY')
    monkeypatch.setenv('PLATPRICES_REGION','us')
    calls=[]
    def request(path,params,key):
        calls.append((path,params,key))
        assert key=='SYNTHETIC_PROVIDER_KEY'
        if path=='/games/search':return [copy.deepcopy(GAME)]
        if path.endswith('/trophies'):return copy.deepcopy(TROPHIES)
        return copy.deepcopy(GAME)
    monkeypatch.setattr(platprices,'request_json',request)
    return calls

def seed(client,source='ps5_native',title_id=KEY['title_id']):
    _,_,token=paired(client,local=uuid.uuid4().hex)
    with Session() as db:
        for identity,name,grade,hidden in [('0','First step','bronze',False),('4','Secret ending','gold',True),('9','DLC trophy','silver',False)]:
            db.add(Record(id=str(uuid.uuid4()),profile=token['profile_uuid'],source=source,kind='trophy',
                key=title_id+':'+identity,mock=False,data={'title_id':title_id,'title':'SYNTHETIC Game',
                    'trophy_id':identity,'name':name,'grade':grade,'hidden':hidden,'unlocked':False}))
            if not db.get(TrophyText,(source,title_id,identity,'en-US')):
                db.add(TrophyText(source=source,title_id=title_id,trophy_id=identity,language='en-US',name=name,description='',is_default=True))
                db.add(TrophyInfo(source=source,title_id=title_id,trophy_id=identity,hidden=hidden,description='SECRET DESCRIPTION' if hidden else ''))
        db.commit()
    return token

def note(client,**changes):
    return client.post('/account/games/howlongtobeat',json={**KEY,'hltb_id':123,'main_seconds':7200,
        'extra_seconds':None,'completionist_seconds':36000,**changes})

def select_listing(client,ppid=123,**key):
    return client.post('/account/games/platprices',json={**KEY,**key,'platprices_id':ppid})

def public(client,visibility='public'):
    handle=social_handle(client)
    assert client.post('/account/profile',json={'handle':handle,'display_name':'SYNTHETIC Player','visibility':visibility}).status_code==200
    return '/players/'+handle+'/games/insights?source=ps5_native&title_id='+KEY['title_id']

def test_completion_estimates_are_owned_separate_and_not_console_state(fake_provider):
    owner,other=browser(),browser('other@example.test');seed(owner);seed(other)
    assert note(owner).status_code==200
    data=owner.get(PATH).json()['howlongtobeat']
    assert data['main_seconds']==7200 and data['extra_seconds'] is None
    assert data['url']=='https://howlongtobeat.com/game/123' and data['entry_mode']=='manual'
    assert other.get(PATH).json()['howlongtobeat']['main_seconds'] is None
    seed(owner,'ps4_bc')
    assert owner.get(PATH.replace('ps5_native','ps4_bc')).json()['howlongtobeat']['hltb_id'] is None
    assert note(owner,main_seconds=None,hltb_id=None).json()['howlongtobeat']['main_seconds'] is None
    assert all(not row['data']['unlocked'] for row in owner.get('/account/library').json())
    assert not fake_provider

def test_every_route_checks_auth_and_game_ownership_before_provider(fake_provider):
    owner=browser();seed(owner);other=browser('other@example.test');anon=TestClient(app)
    for client in (other,anon):
        expected=404 if client is other else 401
        assert client.get(PATH).status_code==expected
        assert client.get('/account/integrations/platprices/search?source=ps5_native&title_id='+KEY['title_id']).status_code==expected
        assert select_listing(client).status_code in (expected,403)
        assert note(client).status_code in (expected,403)
    assert anon.get('/account/integrations').status_code==401
    assert anon.get('/account/integrations/playtime.csv').status_code==401
    owner.headers['origin']='https://wrong.invalid'
    assert note(owner).status_code==403
    assert not fake_provider

@pytest.mark.parametrize('change',[{'main_seconds':-1},{'extra_seconds':0},{'main_seconds':True},
    {'main_seconds':1.2},{'completionist_seconds':36000001},{'hltb_id':0},{'hltb_id':2**40},
    {'source':'psn'},{'title_id':'../secret'},{'unexpected':'value'}])
def test_estimate_validation(change):
    owner=browser();seed(owner)
    assert note(owner,**change).status_code==422

def test_secret_metadata_never_leaves_the_rate_adapter_and_dlc_stays_unknown(fake_provider):
    owner=browser();seed(owner)
    search=owner.get('/account/integrations/platprices/search?source=ps5_native&title_id='+KEY['title_id'])
    assert search.json()['games']==[{'id':123,'title':'SYNTHETIC Game','platform':'PS5','url':'https://platprices.com/game/123'}]
    response=select_listing(owner)
    assert response.status_code==200,response.text
    rarity=response.json()['rarity']
    assert rarity['rates']=={'0':0,'4':None} and '9' not in rarity['rates']
    assert 'Secret ending' not in response.text and 'SECRET DESCRIPTION' not in response.text
    assert 'SYNTHETIC_PROVIDER_KEY' not in response.text
    assert owner.get(PATH).json()['rarity']['rates']==rarity['rates']
    assert len(fake_provider)==3
    assert select_listing(owner,None).json()['rarity']['listing'] is None

def test_shared_access_hiding_revoke_and_no_public_quota_consumption(fake_provider):
    owner=browser();token=seed(owner);note(owner)
    path=public(owner,'friends');anon=TestClient(app)
    assert anon.get(path).status_code==403
    public(owner);assert anon.get(path).json()['howlongtobeat']['main_seconds']==7200
    assert select_listing(owner).status_code==200
    assert anon.get(path).json()['rarity']['rates']=={'0':0,'4':None}
    with Session() as db:
        for row in db.query(ProviderCache).all():row.expires=0
        db.commit()
    assert anon.get(path).json()['rarity']['stale'] is True
    assert len(fake_provider)==2
    owner.post('/account/games/visibility',json={**KEY,'hidden':True})
    assert anon.get(path).status_code==404
    assert owner.get(PATH).status_code==200
    calls_after_owner_refresh=len(fake_provider)
    assert calls_after_owner_refresh==4
    owner.post('/account/devices/'+token['profile_uuid']+'/revoke',json={})
    assert owner.get(PATH).status_code==404 and anon.get(path).status_code==404
    assert len(fake_provider)==calls_after_owner_refresh

def test_provider_does_not_guess_platform_names_grades_or_ordinal_ids(monkeypatch):
    owner=browser();seed(owner)
    original=platprices.request_json
    def wrong(path,params,key):
        value=original(path,params,key)
        if path.endswith('/trophies'):value['trophies'][0]['grade']='gold'
        return value
    monkeypatch.setattr(platprices,'request_json',wrong)
    assert select_listing(owner).status_code==422
    with Session() as db:assert db.query(GameInsight).count()==0
    rows=[{'kind':'trophy','data':{'trophy_id':'0','name':'First step','grade':'bronze'}},
          {'kind':'trophy','data':{'trophy_id':'2','name':'First step','grade':'bronze'}}]
    assert platprices.match_rates(platprices.sanitize('/games/123/trophies',TROPHIES),rows) is None
    assert select_listing(owner,123,source='ps4_bc').status_code==404

def test_cached_failures_retry_after_and_stale_success_are_bounded(monkeypatch,fake_provider):
    owner=browser();seed(owner);assert select_listing(owner).status_code==200
    with Session() as db:
        for row in db.query(ProviderCache).all():row.expires=0
        db.commit()
    failures=[]
    def offline(*args):
        failures.append(True);raise platprices.ProviderError('rate_limited',7200)
    monkeypatch.setattr(platprices,'request_json',offline)
    response=owner.get(PATH).json()['rarity']
    assert response['rates']=={'0':0,'4':None} and response['stale']
    assert response['status']=='rate_limited'
    owner.get(PATH)
    owner.get('/account/integrations/platprices/search?source=ps5_native&title_id='+KEY['title_id'])
    assert len(failures)==1
    assert platprices.retry_seconds('900')==900 and platprices.retry_seconds('0')==60
    assert platprices.retry_seconds('invalid')==3600

@pytest.mark.parametrize('value',[float('nan'),float('inf'),101,-0.1,True,'invalid'])
def test_invalid_percentages_are_rejected(value):
    data=copy.deepcopy(TROPHIES);data['trophies'][0]['earned_rate']=value
    with pytest.raises(platprices.ProviderError):platprices.sanitize('/games/123/trophies',data)

def test_duplicate_provider_ids_partial_roster_and_invalid_types():
    data=copy.deepcopy(TROPHIES);data['trophies'][1]['id']=700
    with pytest.raises(platprices.ProviderError):platprices.sanitize('/games/123/trophies',data)
    for data in [None,[],{'trophies':[],'total':4,'ppid':123}]:
        with pytest.raises(platprices.ProviderError):platprices.sanitize('/games/123/trophies',data)

@pytest.mark.parametrize('status,headers,body,expected',[
    (302,{'location':'https://elsewhere.invalid' },b'', 'unavailable'),
    (429,{'retry-after':'7200'},b'', 'rate_limited'),
    (403,{},b'PRIVATE BODY','configuration_error'),
    (404,{},b'', 'not_found'),
    (200,{'content-type':'text/html'},b'html','invalid_response'),
    (200,{'content-type':'application/json'},b'{}','invalid_response'),
    (200,{'content-type':'application/json'},b'x'*(platprices.MAX_BODY+1),'invalid_response'),
])
def test_transport_limits_redirects_and_sanitized_errors(monkeypatch,status,headers,body,expected):
    original=httpx.Client
    requests=[]
    def mock(request):
        requests.append(request)
        return httpx.Response(status,headers=headers,content=body)
    def client(**kwargs):
        assert kwargs['follow_redirects'] is False and kwargs['trust_env'] is False
        assert kwargs.get('verify',True) is True
        return original(transport=httpx.MockTransport(mock),**kwargs)
    monkeypatch.setattr(httpx,'Client',client)
    with pytest.raises(platprices.ProviderError) as error:REAL_REQUEST('/games/123',{'region':'us'},'PRIVATE_KEY')
    assert error.value.status==expected and 'PRIVATE' not in str(error.value)
    assert len(requests)==1 and requests[0].url.host=='platprices.com'
    assert requests[0].headers['x-api-key']=='PRIVATE_KEY'
    assert 'PRIVATE_KEY' not in str(requests[0].url)

def test_same_cold_cache_is_fetched_once_across_sessions(fake_provider):
    from concurrent.futures import ThreadPoolExecutor
    def query(_):
        with Session() as db:return platprices.cached(db,'/games/123',{})
    with ThreadPoolExecutor(max_workers=3) as pool:responses=list(pool.map(query,range(3)))
    assert all(r['status']=='ok' for r in responses) and len(fake_provider)==1

def test_monthly_budget_prevents_new_upstream_requests(monkeypatch,fake_provider):
    from app.main import digest,now
    from app.models import Rate
    from datetime import datetime,timezone
    credential=platprices.cache_key('SYNTHETIC_PROVIDER_KEY')
    month=datetime.now(timezone.utc).strftime('%Y-%m')
    with Session() as db:
        db.add(Rate(key=digest('platprices-budget:'+credential+month),count=900,reset=now()+86400));db.commit()
        result=platprices.cached(db,'/games/123',{})
        assert result['status']=='rate_limited'
    assert not fake_provider

def test_missing_key_never_requests_provider(monkeypatch,fake_provider):
    monkeypatch.delenv('PLATPRICES_API_KEY');owner=browser();seed(owner)
    assert owner.get('/account/integrations').json()['platprices']['configured'] is False
    assert owner.get(PATH).json()['rarity']['status']=='not_selected'
    assert owner.get(PATH).json()['rarity']['provider']=='exophase'
    assert not fake_provider

def test_csv_is_private_utf8_unknown_preserving_and_formula_safe():
    owner=browser();token=seed(owner)
    with Session() as db:
        row=db.query(Record).first();row.data={**row.data,'title':'=FORMULA Café'};db.commit()
    response=owner.get('/account/integrations/playtime.csv')
    assert response.status_code==200 and response.content.startswith(b'\xef\xbb\xbf')
    assert "'=FORMULA Café,PS5,,0,3" in response.text
    assert 'no-store' in response.headers['cache-control']
    assert token['profile_uuid'] not in response.text
    assert "'\t="==__import__('app.insights',fromlist=['csv_cell']).csv_cell('\t=')
