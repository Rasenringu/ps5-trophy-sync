"""Synthetic HLTB protocol/cache fixtures, distinct from recorded live lookup."""
import copy
import json
from concurrent.futures import ThreadPoolExecutor
import httpx
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db import Session
from app.models import ProviderCache
from app import howlongtobeat as hltb
from app.platprices import ProviderError
from test_flow import reset,browser,social_handle
from test_insights import seed,KEY,PATH,note,public

GAME={'hltb_id':123,'title':'SYNTHETIC Game','platforms':['PlayStation 5','PC'],
      'url':'https://howlongtobeat.com/game/123','main_seconds':900,'extra_seconds':None,'completionist_seconds':7200}
RAW={'game_id':123,'game_name':'SYNTHETIC Game','profile_platform':'PC, PlayStation 5',
     'comp_main':900,'comp_plus':0,'comp_100':7200}
REAL_FETCH=hltb.fetch

@pytest.fixture(autouse=True)
def provider(monkeypatch):
    monkeypatch.setenv('HLTB_ENABLED','true');monkeypatch.delenv('PLATPRICES_API_KEY',raising=False)
    calls=[]
    def fetch(kind,query,platform):
        calls.append((kind,query,platform));return copy.deepcopy(GAME) if kind=='detail' else {'games':[copy.deepcopy(GAME)]}
    monkeypatch.setattr(hltb,'fetch',fetch)
    return calls

def test_automatic_exact_match_preserves_subhour_and_unknown_values(provider):
    owner=browser();seed(owner)
    response=owner.get(PATH);assert response.status_code==200,response.text
    data=response.json()['howlongtobeat']
    assert data['entry_mode']=='provider' and data['status']=='ok'
    assert data['hltb_id']==123 and data['main_seconds']==900 and data['extra_seconds'] is None
    owner.get(PATH);assert len(provider)==1
    assert all(not r['data']['unlocked'] for r in owner.get('/account/library').json())

def test_manual_override_clear_and_return_to_automatic(provider):
    owner=browser();seed(owner)
    assert note(owner).json()['howlongtobeat']['entry_mode']=='manual'
    assert owner.get(PATH).json()['howlongtobeat']['main_seconds']==7200 and not provider
    cleared=note(owner,hltb_id=None,main_seconds=None,completionist_seconds=None).json()['howlongtobeat']
    assert cleared['main_seconds'] is None and cleared['entry_mode']=='manual'
    response=owner.post('/account/games/howlongtobeat/automatic',json=KEY)
    assert response.status_code==200 and response.json()['howlongtobeat']['main_seconds']==900
    assert len(provider)==1

@pytest.mark.parametrize('games',[
    [{**GAME,'title':'SYNTHETIC Game 2'}],
    [{**GAME,'title':'SYNTHETIC Game Remastered'}],
    [GAME,{**GAME,'hltb_id':456}],
    [{**GAME,'platforms':['PlayStation 4']}],
])
def test_no_automatic_sequel_edition_ambiguous_or_cross_platform_match(monkeypatch,games):
    monkeypatch.setattr(hltb,'fetch',lambda *args:{'games':copy.deepcopy(games)})
    owner=browser();seed(owner)
    data=owner.get(PATH).json()['howlongtobeat']
    assert data['main_seconds'] is None and data['status']=='needs_match'

@pytest.mark.parametrize('local,remote',[('N++','N+'),('Rock & Roll','Rock Roll')])
def test_title_symbols_that_change_game_identity_are_preserved(monkeypatch,local,remote):
    monkeypatch.setattr(hltb,'fetch',lambda *args:{'games':[{**GAME,'title':remote}]})
    with Session() as db:
        result=hltb.resolve(db,local,'PlayStation 5')
        assert result['game'] is None and result['status']=='needs_match'

def test_selection_and_search_require_ownership_and_platform(provider,monkeypatch):
    owner=browser();seed(owner);other=browser('other@example.test')
    path='/account/integrations/howlongtobeat/search?source=ps5_native&title_id='+KEY['title_id']
    assert other.get(path).status_code==404
    assert other.post('/account/games/howlongtobeat/automatic',json={**KEY,'hltb_id':123}).status_code==404
    assert not provider
    assert owner.get(path).json()['candidates'][0]['hltb_id']==123
    assert owner.post('/account/games/howlongtobeat/automatic',json={**KEY,'hltb_id':123}).status_code==200
    # A returned detail must match the requested numeric ID and its platform.
    monkeypatch.setattr(hltb,'fetch',lambda *args:{**GAME,'hltb_id':456,'platforms':['PlayStation 4']})
    assert owner.post('/account/games/howlongtobeat/automatic',json={**KEY,'hltb_id':456}).status_code==422

def test_public_reads_only_cache_and_checks_privacy_first(provider):
    owner=browser();token=seed(owner);path=public(owner);anon=TestClient(app)
    assert anon.get(path).json()['howlongtobeat']['status']=='not_cached' and not provider
    owner.get(PATH)
    assert anon.get(path).json()['howlongtobeat']['main_seconds']==900 and len(provider)==1
    with Session() as db:
        for row in db.query(ProviderCache).all():row.expires=0
        db.commit()
    assert anon.get(path).json()['howlongtobeat']['stale'] is True and len(provider)==1
    owner.post('/account/games/visibility',json={**KEY,'hidden':True})
    assert anon.get(path).status_code==404 and len(provider)==1
    owner.post('/account/devices/'+token['profile_uuid']+'/revoke',json={})
    assert owner.get(PATH).status_code==404 and len(provider)==1

def test_outage_preserves_cache_and_applies_global_pause(monkeypatch,provider):
    owner=browser();seed(owner);owner.get(PATH)
    with Session() as db:
        for row in db.query(ProviderCache).all():row.expires=0
        db.commit()
    attempts=[]
    def blocked(*args):attempts.append(1);raise ProviderError('blocked',3600)
    monkeypatch.setattr(hltb,'fetch',blocked)
    data=owner.get(PATH).json()['howlongtobeat']
    assert data['main_seconds']==900 and data['stale'] and data['status']=='blocked'
    owner.get(PATH)
    owner.post('/account/games/howlongtobeat/automatic',json={**KEY,'hltb_id':123})
    assert len(attempts)==1

def test_concurrent_cold_lookup_fetches_once(provider):
    def query(_):
        with Session() as db:return hltb.cached(db,'search','SYNTHETIC Game','PlayStation 5')
    with ThreadPoolExecutor(max_workers=3) as pool:responses=list(pool.map(query,range(3)))
    assert all(r['status']=='ok' for r in responses) and len(provider)==1

def test_detail_identity_schema_unknowns_and_subhour_accuracy():
    raw=b'<script id="__NEXT_DATA__" type="application/json">'+json.dumps({'props':{'pageProps':{'game':{'data':{'game':[RAW]}}}}}).encode()+b'</script>'
    assert hltb.parse_detail(raw,123)['main_seconds']==900
    assert hltb.parse_detail(raw,123)['extra_seconds'] is None
    for identity,body in [(124,raw),(123,b'<script>evil()</script>'),(123,raw.replace(b'900',b'-1'))]:
        with pytest.raises(ProviderError):hltb.parse_detail(body,identity)
    for value in [True,-1,float('nan'),36000001]:
        with pytest.raises(ProviderError):hltb.parse_game({**RAW,'comp_main':value})

def test_anonymous_token_is_volatile_and_search_posts_only_public_query(monkeypatch):
    original=httpx.Client;requests=[]
    def handle(request):
        requests.append(request)
        if request.method=='GET':return httpx.Response(200,json={'token':'SYNTHETIC_ANONYMOUS_TOKEN'})
        assert request.url.path=='/api/search/site' and request.headers['x-auth-token']=='SYNTHETIC_ANONYMOUS_TOKEN'
        assert request.headers.get('cookie') is None
        assert json.loads(request.content)['searchOptions']['games']['userId']==0
        return httpx.Response(200,json={'data':[RAW]})
    def client(**kwargs):
        assert kwargs['follow_redirects'] is False and kwargs['trust_env'] is False and kwargs.get('verify',True) is True
        return original(transport=httpx.MockTransport(handle),**kwargs)
    monkeypatch.setattr(httpx,'Client',client)
    data=REAL_FETCH('search','SYNTHETIC Game','PlayStation 5')
    assert data['games'][0]['main_seconds']==900 and len(requests)==2
    assert all(r.url.host=='howlongtobeat.com' for r in requests)
    assert 'SYNTHETIC_ANONYMOUS_TOKEN' not in json.dumps(data)

def test_disabled_provider_does_not_fetch(monkeypatch,provider):
    monkeypatch.setenv('HLTB_ENABLED','false');owner=browser();seed(owner)
    assert owner.get(PATH).json()['howlongtobeat']['status']=='disabled' and not provider

def test_demon_slayer_search_uses_title_words_and_never_identifiers(monkeypatch):
    calls=[]
    local='Demon Slayer -Kimetsu no Yaiba- The Hinokami Chronicles'
    game={**GAME,'title':'Demon Slayer: Kimetsu no Yaiba - The Hinokami Chronicles','hltb_id':98594}
    sequel={**game,'title':game['title']+' 2','hltb_id':160453}
    def fetch(kind,query,platform):
        calls.append(query);return {'games':[game,sequel]}
    monkeypatch.setattr(hltb,'fetch',fetch)
    with Session() as db:
        result=hltb.resolve(db,local,'PlayStation 5')
    assert result['game']['hltb_id']==98594
    assert calls==['Demon Slayer Kimetsu no Yaiba The Hinokami Chronicles']
    for identity in ['NPWR23868_00','PPSA03457','CUSA02344']:
        with Session() as db:assert hltb.resolve(db,identity,'PlayStation 5')['status']=='title_unavailable'
    assert len(calls)==1

def test_identifier_library_key_is_resolved_to_publisher_title_before_search(provider):
    owner=browser();seed(owner)
    response=owner.get('/account/integrations/howlongtobeat/search?source=ps5_native&title_id='+KEY['title_id'])
    assert response.json()['query']=='SYNTHETIC Game'
    assert provider[0][1]=='SYNTHETIC Game'
