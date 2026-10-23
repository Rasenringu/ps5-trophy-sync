"""Synthetic regressions for console timestamps and missing observation fields."""
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import select
from fastapi.testclient import TestClient
from app.db import Session
from app.models import Profile, Record
from app.main import app
from test_flow import browser, paired, upload, native_activity, native_sample, reset


def test_future_session_dates_do_not_outlive_their_import_or_inflate_totals(monkeypatch):
    import app.main as main
    received = int(datetime(2026, 10, 20, 17, 30, tzinfo=timezone.utc).timestamp())
    monkeypatch.setattr(main, 'now', lambda: received)
    client = browser()
    _, _, device = paired(client)
    body = native_activity(1236)
    body['activities'][0].update(started_at='2026-10-20T19:00:00Z', ended_at='2026-10-20T19:26:05.740Z')
    assert upload(client, device['device_token'], body).status_code == 200
    row = client.get('/account/library').json()[0]['data']
    assert row['started_at'] is None and row['ended_at'] is None
    assert row['timestamp_status'] == 'after_observation'
    assert row['duration_seconds'] == 1236 and row['complete'] is True
    # A later unrelated import must not make this old impossible timestamp valid.
    monkeypatch.setattr(main, 'now', lambda: received + 7 * 86400)
    other = native_activity(60)
    other['activities'][0]['event_id'] = 'native-session:' + 'b' * 64
    other['activities'][0]['native_observation']['session_digest'] = 'b' * 64
    assert upload(client, device['device_token'], other).status_code == 200
    assert client.get('/account/library').json()[0]['data']['ended_at'] is None
    assert upload(client, device['device_token'], body).json()['status'] == 'duplicate'
    with Session() as db:
        raw = db.scalar(select(Record).where(Record.key == body['activities'][0]['event_id'])).data
        assert raw['ended_at'] == '2026-10-20T19:26:05.740000Z'


def test_legacy_future_dates_are_filtered_before_shared_last_played(monkeypatch):
    client = browser()
    _, _, device = paired(client)
    stamp = int(datetime(2026, 10, 20, 17, 30, tzinfo=timezone.utc).timestamp())
    data = native_activity(120)['activities'][0]
    data.update(started_at='2026-10-20T17:20:00Z', ended_at='2026-10-20T19:26:05Z',
                consistency='sqlite_read_transaction', profile_binding='activity_header_single_local_user')
    with Session() as db:
        db.add(Record(id=str(uuid4()), profile=device['profile_uuid'], source='ps5_native',
                      kind='activity', key=data['event_id'], mock=False, data=data))
        db.get(Profile, device['profile_uuid']).last_sync = stamp
        db.commit()
    activity = client.get('/account/library').json()[0]['data']
    assert activity['ended_at'] is None and activity['started_at'] == data['started_at']
    handle = client.get('/account/profile').json()['handle']
    client.post('/account/profile', json={'handle': handle, 'display_name': 'MOCK time', 'visibility': 'public'})
    public = TestClient(app).get('/players/' + handle + '/library').json()[0]['data']
    assert public['last_played_at'] == data['started_at']
    assert public['duration_seconds'] == 120 and public['session_count'] == 1
    assert 'source_timestamps' not in public and 'observed_at' not in public
    # Bootstrapping receipt metadata must retain the old last-sync bound when
    # unchanged legacy timestamps are repeated after a later unrelated sync.
    import app.main as main
    monkeypatch.setattr(main, 'now', lambda: stamp + 7 * 86400)
    unrelated = native_activity(60)
    unrelated['activities'][0]['event_id'] = 'native-session:' + 'b' * 64
    unrelated['activities'][0]['native_observation']['session_digest'] = 'b' * 64
    assert upload(client, device['device_token'], unrelated).status_code == 200
    assert client.get('/account/library').json()[0]['data']['ended_at'] is None
    replay = native_activity(120)
    replay['activities'][0].update(started_at=data['started_at'], ended_at=data['ended_at'])
    assert upload(client, device['device_token'], replay).status_code == 200
    assert client.get('/account/library').json()[0]['data']['ended_at'] is None


def test_known_native_trophy_date_is_recovered_from_retained_evidence():
    client = browser()
    _, _, device = paired(client)
    body = native_sample()
    body['mock'] = False
    body['trophies'][0].update(unlocked_at=None, clock='unknown')
    assert upload(client, device['device_token'], body).status_code == 200
    trophy = client.get('/account/library').json()[0]['data']
    assert trophy['unlocked'] is True
    assert trophy['unlocked_at'] == '2026-10-06T22:07:00Z'
    assert trophy['clock'] == 'uncertain'


def test_recovered_unlock_date_keeps_its_original_receipt_bound(monkeypatch):
    import app.main as main
    received = int(datetime(2026, 10, 6, 20, tzinfo=timezone.utc).timestamp())
    monkeypatch.setattr(main, 'now', lambda: received)
    client = browser()
    _, _, device = paired(client)
    body = native_sample()
    body['mock'] = False
    body['trophies'][0].update(unlocked_at=None, clock='unknown')
    assert upload(client, device['device_token'], body).status_code == 200
    trophy = client.get('/account/library').json()[0]['data']
    assert trophy['unlocked_at'] is None and trophy['timestamp_status'] == 'after_observation'
    monkeypatch.setattr(main, 'now', lambda: received + 7 * 86400)
    assert upload(client, device['device_token'], native_activity()).status_code == 200
    trophy = next(r['data'] for r in client.get('/account/library').json() if r['kind'] == 'trophy')
    assert trophy['unlocked_at'] is None


def test_unknown_native_flags_and_incomplete_session_remain_explicit():
    client = browser()
    _, _, device = paired(client)
    body = native_sample()
    body['mock'] = False
    body['trophies'][0].update(unlocked=None, unlocked_at=None, clock='unknown',
                             native_observation={'raw_flags': 18, 'first_raw': '0', 'second_raw': '63926921220000000'})
    assert upload(client, device['device_token'], body).status_code == 200
    assert upload(client, device['device_token'], native_activity(complete=False)).status_code == 200
    rows = client.get('/account/library').json()
    trophy = next(r['data'] for r in rows if r['kind'] == 'trophy')
    activity = next(r['data'] for r in rows if r['kind'] == 'activity')
    assert trophy['unlocked'] is None and trophy['state_reason'] == 'unsupported_native_flags'
    assert trophy['unlocked_at'] is None
    assert activity['duration_seconds'] is None and activity['duration_reason'] == 'missing_session_end'


def test_verified_locked_pattern_repairs_existing_unknown_rows_without_resync():
    client = browser()
    _, _, device = paired(client)
    body = native_sample()
    body['mock'] = False
    body['trophies'][0].update(title_id='NPWR57054_00', unlocked=None, unlocked_at=None, clock='unknown',
                             native_observation={'raw_flags': 16, 'first_raw': '0', 'second_raw': '63926921220000000'})
    assert upload(client, device['device_token'], body).status_code == 200
    row = client.get('/account/library').json()[0]['data']
    assert row['unlocked'] is False and row['observed_unlock_state'] is False
    assert row['unlocked_at'] is None and row['clock'] == 'unknown'
    assert 'state_reason' not in row
    assert upload(client, device['device_token'], body).json()['status'] == 'duplicate'
    with Session() as db:
        raw = db.scalar(select(Record)).data
        assert raw['unlocked'] is None and raw['native_observation']['second_raw'] == '63926921220000000'
    # New workers can state the verified locked result with identical raw evidence.
    body['batch_id'] = str(uuid4())
    body['trophies'][0]['unlocked'] = False
    assert upload(client, device['device_token'], body).status_code == 200
    assert client.get('/account/library').json()[0]['data']['unlocked'] is False
    # A known earned observation must still survive a later locked observation.
    earned = native_sample()
    earned['mock'] = False
    earned['trophies'][0]['title_id'] = 'NPWR57054_00'
    assert upload(client, device['device_token'], earned).status_code == 200
    body['batch_id'] = str(uuid4())
    assert upload(client, device['device_token'], body).status_code == 200
    assert client.get('/account/library').json()[0]['data']['unlocked'] is True


def test_unverified_flag16_variants_are_not_promoted_to_locked():
    from app.observation_times import present_observation
    from app.contracts import NativeTrophy
    from pydantic import ValidationError
    import pytest
    for first, second in [('1', '63926921220000000'), ('0', '0'), ('0', '1'), ('0', '18446744073709551615')]:
        raw = {'unlocked': None, 'unlocked_at': None, 'clock': 'unknown',
               'native_observation': {'raw_flags': 16, 'first_raw': first, 'second_raw': second}}
        assert present_observation(raw, 'trophy', 'ps5_native', 1800000000)['unlocked'] is None
        claimed = {**native_sample()['trophies'][0], **raw, 'unlocked': False}
        with pytest.raises(ValidationError):
            NativeTrophy.model_validate(claimed)


def test_shared_undated_incomplete_game_is_visible_without_a_fabricated_total():
    client = browser()
    _, _, device = paired(client)
    body = native_activity(complete=False)
    body['activities'][0].update(started_at=None, ended_at=None, clock='unknown')
    assert upload(client, device['device_token'], body).status_code == 200
    handle = client.get('/account/profile').json()['handle']
    client.post('/account/profile', json={'handle': handle, 'display_name': 'MOCK time', 'visibility': 'public'})
    public = TestClient(app).get('/players/' + handle + '/library').json()
    assert len(public) == 1
    assert public[0]['data']['title_id'] == 'PPSA12345'
    assert public[0]['data']['duration_seconds'] is None
    assert public[0]['data']['session_count'] == 0
    assert public[0]['data']['last_played_at'] is None
