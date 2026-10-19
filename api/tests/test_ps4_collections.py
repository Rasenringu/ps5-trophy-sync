"""MOCK state/activity fixtures; publisher membership has separate FTP evidence."""
import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from app.main import app
from test_flow import browser, paired, upload, native_activity, social_handle, reset
from test_ps4 import package, snapshot

APPLICATION = 'CUSA02344'
FIRST = 'NPWR09798_00'
SECOND = 'NPWR09799_00'


def activity(application=APPLICATION, seconds=120):
    body = native_activity(seconds)
    body['activities'][0].update(title_id=application, title='MOCK collection')
    body['activities'][0]['native_observation']['application_title_id'] = application
    return body


def add_set(owner, device, title=FIRST, application='CUSA03280'):
    raw = package(title)
    body = snapshot(raw, title, application)
    assert upload(owner, device['device_token'], body).status_code == 200
    assert owner.post('/device/ps4-artwork/' + title, headers={
        'authorization': 'Bearer ' + device['device_token'],
        'content-type': 'application/octet-stream'}, content=raw).status_code == 200
    return body


@pytest.mark.parametrize('binding', ['CUSA03280', APPLICATION])
def test_collection_links_existing_component_state_once_and_preserves_trophy_identity(binding):
    owner = browser()
    _, _, device = paired(owner)
    body = add_set(owner, device, application=binding)
    session = activity()
    for _ in range(2):
        assert upload(owner, device['device_token'], body).status_code == 200
        assert upload(owner, device['device_token'], session).status_code == 200
    rows = owner.get('/account/library').json()
    assert len(rows) == 3
    assert all(r['source'] == 'ps4_bc' and r['data']['collection_title_id'] == APPLICATION for r in rows)
    assert {r['data']['title_id'] for r in rows if r['kind'] == 'trophy'} == {FIRST}
    assert not any(r['data']['title_id'] in (SECOND, 'NPWR09801_00') for r in rows)
    sessions = [r for r in rows if r['kind'] == 'activity']
    assert len(sessions) == 1 and sessions[0]['data']['duration_seconds'] == 120
    assert sessions[0]['data']['title_id'] == (APPLICATION if binding != APPLICATION else FIRST)
    assert sessions[0]['data']['activity_source'] == 'ps5_native'
    assert 'collection_component_title_id' not in sessions[0]['data']
    # New component state does not overwrite trophy 0/1 or clone activity.
    add_set(owner, device, SECOND)
    rows = owner.get('/account/library').json()
    assert len(rows) == 5 and len([r for r in rows if r['kind'] == 'activity']) == 1
    assert len({(r['data']['title_id'], r['data']['trophy_id']) for r in rows if r['kind'] == 'trophy'}) == 4


def test_exact_component_activity_and_launcher_are_counted_once_with_collection_artwork():
    from test_artwork import image
    owner = browser()
    _, _, device = paired(owner)
    add_set(owner, device)
    assert upload(owner, device['device_token'], activity()).status_code == 200
    component = activity('CUSA03280', 300)
    component['activities'][0]['event_id'] = 'native-session:' + 'b' * 64
    component['activities'][0]['native_observation']['session_digest'] = 'b' * 64
    assert upload(owner, device['device_token'], component).status_code == 200
    assert owner.post('/device/application-artwork/' + APPLICATION, headers={
        'authorization': 'Bearer ' + device['device_token'],
        'content-type': 'application/octet-stream'}, content=image()).status_code == 200
    rows = owner.get('/account/library').json()
    assert all(r['data']['collection_title_id'] == APPLICATION for r in rows)
    sessions = [r for r in rows if r['kind'] == 'activity']
    assert len(sessions) == 2 and sum(r['data']['duration_seconds'] for r in sessions) == 420
    assert all(r['data']['activity_source'] == 'ps5_native' for r in sessions)
    assert len({r['artwork_url'] for r in rows}) == 1
    assert owner.get(rows[0]['artwork_url'].replace('/api', '', 1)).status_code == 200
    handle = social_handle(owner)
    owner.post('/account/profile', json={'handle': handle, 'display_name': 'MOCK collection player', 'visibility': 'public'})
    anon = TestClient(app)
    shared = anon.get('/players/' + handle + '/library').json()
    component_art = next(r['component_artwork_url'] for r in shared if r['kind'] == 'trophy')
    assert component_art != shared[0]['artwork_url']
    response = anon.get(component_art.replace('/api', '', 1))
    assert response.status_code == 200
    friend = browser('collection-art-friend@example.test')
    request_id = friend.post('/account/friends/request', json={'handle': handle}).json()['request_id']
    owner.post('/account/friends/' + request_id, json={'action': 'accept'})
    compared = friend.get('/account/friends/' + handle + '/compare').json()['games']
    assert len(compared) == 1 and friend.get(compared[0]['artwork_url'].replace('/api', '', 1)).status_code == 200
    owner.post('/account/games/visibility', json={'source': 'ps4_bc', 'title_id': APPLICATION, 'hidden': True})
    assert anon.get(component_art.replace('/api', '', 1), headers={'if-none-match': response.headers['etag']}).status_code == 404
    assert friend.get(compared[0]['artwork_url'].replace('/api', '', 1)).status_code == 404


def test_launcher_and_component_counters_with_same_set_alias_stay_separate_in_shared_groups():
    owner = browser()
    _, _, device = paired(owner)
    body = add_set(owner, device, application=APPLICATION)
    body['batch_id'] = str(uuid4())
    for trophy in body['trophies']:
        trophy['ps4_observation']['application_title_ids'].append('CUSA03280')
    assert upload(owner, device['device_token'], body).status_code == 200
    assert upload(owner, device['device_token'], activity()).status_code == 200
    component = activity('CUSA03280', 300)
    component['activities'][0]['event_id'] = 'native-session:' + 'b' * 64
    component['activities'][0]['native_observation']['session_digest'] = 'b' * 64
    assert upload(owner, device['device_token'], component).status_code == 200
    private = owner.get('/account/library').json()
    sessions = [r for r in private if r['kind'] == 'activity']
    assert len(sessions) == 2 and all(r['data']['title_id'] == FIRST for r in sessions)
    assert sorted((r['data'].get('collection_component_title_id') or '', r['data']['duration_seconds']) for r in sessions) == [('', 120), (FIRST, 300)]
    handle = social_handle(owner)
    owner.post('/account/profile', json={'handle': handle, 'display_name': 'MOCK collection player', 'visibility': 'public'})
    shared = TestClient(app).get('/players/' + handle + '/library').json()
    totals = [r for r in shared if r['kind'] == 'activity']
    assert len(totals) == 2
    assert sorted((r['data'].get('collection_component_title_id') or '', r['data']['duration_seconds'], r['data']['session_count']) for r in totals) == [('', 120, 1), (FIRST, 300, 1)]
    assert 'native_observation' not in str(shared)


def test_collection_needs_owned_same_profile_native_activity_and_observed_state():
    owner = browser()
    _, _, first = paired(owner)
    _, _, second = paired(owner, local='second')
    add_set(owner, first)
    assert upload(owner, second['device_token'], activity()).status_code == 200
    assert all('collection_title_id' not in r['data'] for r in owner.get('/account/library').json())
    other = browser('collection-other@example.test')
    _, _, foreign = paired(other)
    assert upload(other, foreign['device_token'], activity()).status_code == 200
    assert all('collection_title_id' not in r['data'] for r in other.get('/account/library').json())
    # Same title text/another region does not supply a publisher binding.
    assert upload(owner, first['device_token'], activity('CUSA02343')).status_code == 200
    assert all('collection_title_id' not in r['data'] for r in owner.get('/account/library').json())
    assert upload(owner, first['device_token'], activity()).status_code == 200
    rows = owner.get('/account/library').json()
    assert all('collection_title_id' not in r['data'] for r in rows if r['profile_uuid'] == second['profile_uuid'])
    owner.post('/account/devices/' + first['profile_uuid'] + '/revoke', json={})
    assert all('collection_title_id' not in r['data'] for r in owner.get('/account/library').json())


def test_collection_shared_totals_keep_set_relative_secret_privacy_and_hiding():
    owner = browser()
    _, _, device = paired(owner)
    add_set(owner, device)
    add_set(owner, device, SECOND)
    assert upload(owner, device['device_token'], activity()).status_code == 200
    handle = social_handle(owner)
    assert owner.post('/account/profile', json={'handle': handle, 'display_name': 'MOCK collection player', 'visibility': 'public'}).status_code == 200
    anon = TestClient(app)
    path = '/players/' + handle + '/library'
    rows = anon.get(path).json()
    assert len(rows) == 5 and all(r['data']['collection_title_id'] == APPLICATION for r in rows)
    total = next(r['data'] for r in rows if r['kind'] == 'activity')
    assert total['session_count'] == 1 and total['duration_seconds'] == 120
    assert 'native_observation' not in str(rows) and device['profile_uuid'] not in str(rows)
    secrets = [r for r in rows if r['kind'] == 'trophy' and r['data']['trophy_id'] == '1']
    assert len(secrets) == 2 and all(r['data']['name'] == 'Hidden trophy' and not r['icon_url'] for r in secrets)
    # Earning the same numeric trophy in another set must not reveal the first.
    viewer = browser('collection-viewer@example.test')
    _, _, viewer_device = paired(viewer)
    add_set(viewer, viewer_device, SECOND)
    shared = viewer.get(path).json()
    assert next(r for r in shared if r['kind'] == 'trophy' and r['data']['title_id'] == FIRST and r['data']['trophy_id'] == '1')['data']['concealed'] is True
    assert next(r for r in shared if r['kind'] == 'trophy' and r['data']['title_id'] == SECOND and r['data']['trophy_id'] == '1')['data']['concealed'] is False
    image = next(r['artwork_url'] for r in rows if r['kind'] == 'trophy')
    response = anon.get(image.replace('/api', '', 1))
    assert response.status_code == 200
    hide = {'source': 'ps4_bc', 'title_id': APPLICATION, 'hidden': True}
    assert viewer.post('/account/games/visibility', json=hide).status_code == 404
    for _ in range(2):
        assert owner.post('/account/games/visibility', json=hide).status_code == 200
    assert anon.get(path).json() == []
    assert anon.get(image.replace('/api', '', 1), headers={'if-none-match': response.headers['etag']}).status_code == 404
    assert all(r['game_hidden'] for r in owner.get('/account/library').json())
    assert owner.post('/account/games/visibility', json={**hide, 'hidden': False}).status_code == 200
    assert len(anon.get(path).json()) == 5


def test_hidden_activity_preference_survives_later_collection_binding_and_unhide():
    owner = browser()
    _, _, device = paired(owner)
    assert upload(owner, device['device_token'], activity()).status_code == 200
    hide = {'source': 'ps5_native', 'title_id': APPLICATION, 'hidden': True}
    assert owner.post('/account/games/visibility', json=hide).status_code == 200
    add_set(owner, device)
    assert all(r['game_hidden'] for r in owner.get('/account/library').json())
    assert owner.post('/account/games/visibility', json={'source': 'ps4_bc', 'title_id': APPLICATION, 'hidden': False}).status_code == 200
    assert all(not r['game_hidden'] for r in owner.get('/account/library').json())
