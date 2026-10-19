"""Synthetic PS5 identity fixtures; no live-console or production-data writes."""
import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from app.main import app
from app.db import Session
from app.models import Record, TrophyText
from test_flow import browser, paired, upload, native_activity, native_sample, social_handle, reset

CANONICAL = 'Demon Slayer -Kimetsu no Yaiba- The Hinokami Chronicles'
REGIONAL = 'Demon Slayer Kimetsu no Yaiba The Hinokami Chronicles'


def trophies(title=CANONICAL, identity='NPWR23868_00'):
    body = native_sample()
    body.update(mock=False)
    body['trophies'][0].update(title_id=identity, title=title)
    return body


def activity(application='PPSA03457', title=REGIONAL, seconds=1219, session='b'):
    body = native_activity(seconds)
    row = body['activities'][0]
    row.update(title_id=application, title=title, event_id='native-session:' + session * 64)
    row['native_observation'].update(application_title_id=application, session_digest=session * 64)
    return body


def test_ps5_regional_releases_share_trophy_identity_without_reimport_or_duplicate_time():
    owner = browser()
    _, _, device = paired(owner)
    old = activity('PPSA03490', CANONICAL, 1029, 'a')
    new = activity()
    for body in (trophies(), old, new):
        assert upload(owner, device['device_token'], body).status_code == 200
    rows = owner.get('/account/library').json()
    assert {r['data']['title_id'] for r in rows} == {'NPWR23868_00'}
    assert len(rows) == 3 and sum(r['data'].get('duration_seconds') or 0 for r in rows) == 2248
    assert all(r['source'] == 'ps5_native' for r in rows)
    assert next(r for r in rows if r['kind'] == 'trophy')['data']['unlocked'] is True
    for _ in range(2):
        assert upload(owner, device['device_token'], new).status_code == 200
    assert len(owner.get('/account/library').json()) == 3
    with Session() as db:
        stored = list(db.scalars(select(Record).where(Record.kind == 'activity')))
        assert {r.data['title_id'] for r in stored} == {'PPSA03457', 'PPSA03490'}
    handle = social_handle(owner)
    owner.post('/account/profile', json={'handle': handle, 'display_name': 'MOCK identity player', 'visibility': 'public'})
    shared = TestClient(app).get('/players/' + handle + '/library').json()
    assert len(shared) == 2
    summary = next(r['data'] for r in shared if r['kind'] == 'activity')
    assert summary['duration_seconds'] == 2248 and summary['session_count'] == 2
    assert 'native_observation' not in str(shared) and device['profile_uuid'] not in str(shared)


def test_punctuation_normalization_merges_unambiguous_unregistered_ps5_release_names():
    owner = browser()
    _, _, device = paired(owner)
    assert upload(owner, device['device_token'], trophies('MOCK Game — The Journey™', 'NPWR00003_00')).status_code == 200
    assert upload(owner, device['device_token'], activity('PPSA00003', 'mock game the journey')).status_code == 200
    rows = owner.get('/account/library').json()
    assert {r['data']['title_id'] for r in rows} == {'NPWR00003_00'}
    assert next(r for r in rows if r['kind'] == 'activity')['data']['title_binding'] == 'unique_normalized_title_metadata'


@pytest.mark.parametrize('different', ['MOCK Game 2', 'MOCK Game III', 'MOCK Game Remastered', 'MOCK Game Deluxe Edition', 'MOCK Game+'])
def test_sequel_edition_and_meaningful_symbol_differences_do_not_merge(different):
    owner = browser()
    _, _, device = paired(owner)
    assert upload(owner, device['device_token'], trophies('MOCK Game', 'NPWR00003_00')).status_code == 200
    assert upload(owner, device['device_token'], activity('PPSA00003', different)).status_code == 200
    assert {r['data']['title_id'] for r in owner.get('/account/library').json()} == {'NPWR00003_00', 'PPSA00003'}


def test_normalized_names_never_choose_between_independent_trophy_stacks():
    owner = browser()
    _, _, device = paired(owner)
    for title, identity in [('MOCK Game — The Journey', 'NPWR00003_00'), ('MOCK GAME: The Journey', 'NPWR00004_00')]:
        assert upload(owner, device['device_token'], trophies(title, identity)).status_code == 200
    assert upload(owner, device['device_token'], activity('PPSA00003', 'mock game the journey')).status_code == 200
    assert {r['data']['title_id'] for r in owner.get('/account/library').json()} == {'NPWR00003_00', 'NPWR00004_00', 'PPSA00003'}
    assert upload(owner, device['device_token'], activity('PPSA03457', 'MOCK GAME: The Journey', session='d')).status_code == 200
    known = next(r for r in owner.get('/account/library').json() if r['kind'] == 'activity' and r['data']['native_observation']['application_title_id'] == 'PPSA03457')
    assert known['data']['title_id'] == 'PPSA03457'
    # An explicit publisher ID can disambiguate identical names safely.
    assert upload(owner, device['device_token'], trophies('MOCK Known Release', 'NPWR23868_00')).status_code == 200
    assert upload(owner, device['device_token'], activity('PPSA03457', 'MOCK GAME: The Journey', session='c')).status_code == 200
    row = next(r for r in owner.get('/account/library').json() if r['kind'] == 'activity' and r['data']['native_observation']['application_title_id'] == 'PPSA03457')
    assert row['data']['title_id'] == 'NPWR23868_00'
    assert row['data']['title_binding'] == 'verified_native_application_metadata'


def test_matching_cannot_borrow_trophy_state_from_another_profile_account_or_platform():
    owner = browser()
    _, _, first = paired(owner)
    _, _, second = paired(owner, local='second')
    assert upload(owner, first['device_token'], trophies()).status_code == 200
    assert upload(owner, second['device_token'], activity()).status_code == 200
    assert next(r for r in owner.get('/account/library').json() if r['kind'] == 'activity')['data']['title_id'] == 'PPSA03457'
    foreign = browser('native-identity-other@example.test')
    _, _, foreign_device = paired(foreign)
    assert upload(foreign, foreign_device['device_token'], activity()).status_code == 200
    assert foreign.get('/account/library').json()[0]['data']['title_id'] == 'PPSA03457'
    # CUSA logger activity remains PS4 even with a matching title.
    assert upload(owner, first['device_token'], activity('CUSA00003', CANONICAL)).status_code == 200
    row = next(r for r in owner.get('/account/library').json() if r['kind'] == 'activity' and r['profile_uuid'] == first['profile_uuid'])
    assert row['data']['title_id'] == 'CUSA00003'
    owner.post('/account/devices/' + first['profile_uuid'] + '/revoke', json={})
    assert all(r['data']['title_id'] == 'PPSA03457' for r in owner.get('/account/library').json())


def test_native_regional_name_uses_verified_package_translations_in_any_browser_language():
    from test_artwork import package, image
    owner = browser()
    _, _, device = paired(owner)
    identity = 'NPWR00003_00'
    assert upload(owner, device['device_token'], trophies('MOCK English: The Journey', identity)).status_code == 200
    assert upload(owner, device['device_token'], activity('PPSA00003', 'MOCK Français Le Voyage')).status_code == 200
    conf = {'schemaVersion': '1.00', 'platform': ['PS5'], 'trophyNpCommId': identity,
            'trophyDefinitionRevision': '1', 'trophySetVersion': '1', 'defaultLanguage': 'en-US',
            'trophies': [{'id': '0', 'grade': 'G', 'hidden': False}]}
    def metadata(label):
        return {**{k:conf[k] for k in ('trophyNpCommId', 'trophyDefinitionRevision', 'trophySetVersion')},
                'schemaVersion': '0.90', 'metadata': {'titleMetadata': {'name': label},
                'trophyMetadata': [{'id': '0', 'name': 'MOCK trophy', 'detail': 'MOCK detail'}]}}
    raw = package({'tropconf.json': json.dumps(conf).encode(),
                   'tropmeta_en-US.json': json.dumps(metadata('MOCK English: The Journey')).encode(),
                   'tropmeta_fr-FR.json': json.dumps(metadata('MOCK Français — Le Voyage')).encode(),
                   'icon0.png': image(), 'trop0000.png': image()})
    assert owner.post('/device/artwork', headers={'authorization': 'Bearer ' + device['device_token'],
                      'content-type': 'application/octet-stream'}, content=raw).status_code == 200
    for language, expected in [('en-US', 'MOCK English: The Journey'), ('fr-FR', 'MOCK Français — Le Voyage')]:
        rows = owner.get('/account/library?language=' + language).json()
        assert len(rows) == 2 and all(r['data']['title_id'] == identity and r['data']['title'] == expected for r in rows)
    # The separately validated global translation cache also supplies title names.
    with Session() as db:
        db.add(TrophyText(source='ps5_native', title_id=identity, trophy_id='', language='es-ES',
            name='MOCK Español: El Viaje', description='', is_default=False))
        db.commit()
    assert upload(owner, device['device_token'], activity('PPSA00004', 'mock español el viaje', session='c')).status_code == 200
    assert all(r['data']['title_id'] == identity for r in owner.get('/account/library').json())


def test_hidden_release_preference_survives_canonical_merge_and_unhide():
    from test_artwork import image
    owner = browser()
    _, _, device = paired(owner)
    assert upload(owner, device['device_token'], activity()).status_code == 200
    assert owner.post('/device/application-artwork/PPSA03457', headers={'authorization': 'Bearer ' + device['device_token'],
                      'content-type': 'application/octet-stream'}, content=image()).status_code == 200
    handle = social_handle(owner)
    owner.post('/account/profile', json={'handle': handle, 'display_name': 'MOCK hidden release', 'visibility': 'public',
        'favorite': {'source': 'ps5_native', 'title_id': 'PPSA03457'}})
    shared_path = '/players/' + handle + '/library'
    anon = TestClient(app)
    before = anon.get(shared_path).json()
    art = before[0]['artwork_url'].replace('/api', '', 1)
    response = anon.get(art)
    assert response.status_code == 200
    assert owner.post('/account/games/visibility', json={'source': 'ps5_native', 'title_id': 'PPSA03457', 'hidden': True}).status_code == 200
    assert upload(owner, device['device_token'], trophies()).status_code == 200
    rows = owner.get('/account/library').json()
    assert len(rows) == 2 and all(r['game_hidden'] and r['data']['title_id'] == 'NPWR23868_00' for r in rows)
    assert anon.get(shared_path).json() == []
    assert anon.get(art, headers={'if-none-match': response.headers['etag']}).status_code == 404
    assert owner.post('/account/games/visibility', json={'source': 'ps5_native', 'title_id': 'NPWR23868_00', 'hidden': False}).status_code == 200
    assert len(anon.get(shared_path).json()) == 2
    assert owner.get('/account/profile').json()['favorite'] == {'source': 'ps5_native', 'title_id': 'NPWR23868_00'}
    favorite = anon.get('/players/' + handle).json()['favorite']
    assert favorite['title_id'] == 'NPWR23868_00'
    assert owner.post('/account/profile', json={'handle': handle, 'display_name': 'MOCK restored favorite',
        'favorite': {'source': 'ps5_native', 'title_id': 'PPSA03457'}}).json()['favorite']['title_id'] == 'NPWR23868_00'
