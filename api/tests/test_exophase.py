"""Synthetic public listing fixtures. No live provider/console requests."""
import copy
import httpx
import pytest
from fastapi.testclient import TestClient
from app import exophase
from app.main import app
from app.db import Session
from app.models import ProviderCache
from app.platprices import ProviderError
from test_flow import reset,browser
from test_insights import seed,KEY,PATH,public

SLUG='synthetic-game-psn'
URL=exophase.BASE+'/game/'+SLUG+'/trophies/'
PAGE=b'''<meta property="og:title" content="SYNTHETIC Game"><strong>2</strong><span>Total Trophies</span>
<ul class="psn trophy platform-ps5">
<li class="award visible" data-master="100" data-average="0.00"><div class="award-title"><a>First step</a></div><i class="exo-icon-trophy-bronze"></i></li>
<li class="award secret" data-master="200"><div class="award-title"><a>Secret ending</a></div><i class="exo-icon-trophy-gold"></i></li></ul>'''
REAL_FETCH=exophase.fetch

@pytest.fixture(autouse=True)
def provider(monkeypatch):
    calls=[]
    def fetch(slug):calls.append(slug);return exophase.parse(PAGE,slug)
    monkeypatch.setattr(exophase,'fetch',fetch)
    return calls

def select(client,url=URL):return client.post('/account/games/trophy-rates',json={**KEY,'listing_url':url})

def test_keyless_listing_rates_cache_secret_privacy_and_removal(monkeypatch,provider):
    monkeypatch.delenv('PLATPRICES_API_KEY',raising=False)
    owner=browser();seed(owner)
    assert owner.get(PATH).json()['rarity']['provider']=='exophase'
    assert provider==[]
    response=select(owner);assert response.status_code==200,response.text
    data=response.json()['rarity']
    assert data['rates']=={'0':0,'4':None} and data['provider']=='exophase'
    assert data['listing']['url']==URL and 'Secret ending' not in response.text
    owner.get(PATH);assert provider==[SLUG]
    assert select(owner,None).json()['rarity']['rates']=={}

def test_ownership_hidden_revoked_and_shared_cache_only(provider):
    owner=browser();token=seed(owner);other=browser('other@example.test')
    assert select(other).status_code==404 and provider==[]
    path=public(owner);anon=TestClient(app)
    select(owner)
    assert anon.get(path).json()['rarity']['rates']=={'0':0,'4':None} and provider==[SLUG]
    owner.post('/account/games/visibility',json={**KEY,'hidden':True})
    assert anon.get(path).status_code==404
    owner.post('/account/devices/'+token['profile_uuid']+'/revoke',json={})
    assert select(owner).status_code==404 and provider==[SLUG]

@pytest.mark.parametrize('change',[
    (b'platform-ps5',b'platform-ps4'),(b'Secret ending',b'Other game trophy'),
])
def test_platform_and_entire_returned_roster_are_required(monkeypatch,change):
    monkeypatch.setattr(exophase,'fetch',lambda slug:exophase.parse(PAGE.replace(*change),slug))
    owner=browser();seed(owner);assert select(owner).status_code==422

@pytest.mark.parametrize('url',['http://www.exophase.com/game/a/trophies/','https://evil.test/game/a/trophies/',
    'https://www.exophase.com@evil.test/game/a/trophies/','https://www.exophase.com/game/a/../b/trophies/',
    'https://www.exophase.com/game/a/trophies/?token=secret','https://www.exophase.com/game/a/trophies/#fragment'])
def test_listing_url_cannot_choose_host_path_or_query(url,provider):
    owner=browser();seed(owner);assert select(owner,url).status_code==422 and not provider

@pytest.mark.parametrize('old,new',[(b'2</strong>',b'3</strong>'),(b'0.00',b'nan'),(b'0.00',b'100.1'),
    (b'0.00',b'-1'),(b'data-master="200"',b'data-master="100"'),(b'exo-icon-trophy-gold',b'exo-icon-unknown')])
def test_malformed_incomplete_duplicate_or_unknown_grade_fails_closed(old,new):
    with pytest.raises(ProviderError):exophase.parse(PAGE.replace(old,new),SLUG)

def test_provider_block_pauses_other_listings_and_keeps_prior_rates(monkeypatch,provider):
    owner=browser();seed(owner);select(owner)
    with Session() as db:
        for row in db.query(ProviderCache).all():row.expires=0
        db.commit()
    calls=[]
    def blocked(slug):calls.append(slug);raise ProviderError('blocked')
    monkeypatch.setattr(exophase,'fetch',blocked)
    data=owner.get(PATH).json()['rarity']
    assert data['stale'] and data['rates']['0']==0 and data['status']=='blocked'
    with Session() as db:assert exophase.cached(db,'other-game')['status']=='blocked'
    assert calls==[SLUG]

def test_fixed_origin_tls_redirect_and_body_bounds(monkeypatch):
    original=httpx.Client;requests=[]
    def handle(request):requests.append(request);return httpx.Response(200,headers={'content-type':'text/html'},content=PAGE)
    def client(**kwargs):
        assert kwargs['follow_redirects'] is False and kwargs['trust_env'] is False and kwargs.get('verify',True) is True
        return original(transport=httpx.MockTransport(handle),**kwargs)
    monkeypatch.setattr(httpx,'Client',client)
    assert REAL_FETCH(SLUG)['trophies'][0]['rate']==0
    assert str(requests[0].url)==URL and 'cookie' not in requests[0].headers
    monkeypatch.setattr(exophase,'MAX_BODY',10)
    with pytest.raises(ProviderError):REAL_FETCH(SLUG)
