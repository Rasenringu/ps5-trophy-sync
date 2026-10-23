"""Synthetic rejection fixtures; no console or hosted service contacted."""
import copy
import logging

import pytest

from test_flow import browser, native_sample, paired, reset, upload


def test_rejected_batch_is_bounded_private_and_logs_actionable_fields(caplog):
    client = browser()
    _, _, credential = paired(client)
    body = native_sample()
    private = 'MOCK_PRIVATE_SOURCE_VALUE'
    row = body['trophies'][0]
    row.update(title=private * 7, name=private * 7, unlocked=False, unlocked_at=None)
    body['trophies'] = [dict(copy.deepcopy(row), trophy_id=str(i)) for i in range(8)]
    with caplog.at_level(logging.WARNING, logger='uvicorn.error'):
        response = upload(client, credential['device_token'], body)
    assert response.status_code == 422
    assert len(response.content) < 4096
    data = response.json()
    assert data['code'] == 'invalid_snapshot'
    assert data['schema_version'] == 2
    assert len(data['detail']) <= 6 and data['errors_truncated'] is True
    assert all(error['loc'][:3] == ['body', 2, 'trophies'] for error in data['detail'])
    assert 'trophies' in caplog.text and 'value_error' in caplog.text
    for value in (private, body['batch_id'], credential['device_token'], row['native_observation']['first_raw']):
        assert value not in response.text and value not in caplog.text
    assert client.get('/account/library').json() == []
    assert response.headers['cache-control'] == 'no-store'


@pytest.mark.parametrize('version', [None, 'MOCK_PRIVATE_TAG', {'MOCK_PRIVATE_KEY': 'MOCK_PRIVATE_VALUE'}, 99])
def test_unknown_or_missing_schema_has_bounded_nonreflecting_diagnostics(version, caplog):
    client = browser()
    _, _, credential = paired(client)
    body = native_sample()
    if version is None:
        del body['schema_version']
    else:
        body['schema_version'] = version
    with caplog.at_level(logging.WARNING, logger='uvicorn.error'):
        response = upload(client, credential['device_token'], body)
    assert response.status_code == 422 and len(response.content) < 4096
    assert response.json()['code'] == 'invalid_snapshot'
    assert 'MOCK_PRIVATE' not in response.text + caplog.text
    assert body['batch_id'] not in response.text + caplog.text


def test_unknown_field_names_and_values_are_redacted(caplog):
    client = browser()
    _, _, credential = paired(client)
    body = native_sample()
    body['trophies'][0]['MOCK_PRIVATE_FIELD'] = 'MOCK_PRIVATE_VALUE'
    with caplog.at_level(logging.WARNING, logger='uvicorn.error'):
        response = upload(client, credential['device_token'], body)
    assert response.status_code == 422
    assert 'MOCK_PRIVATE' not in response.text + caplog.text
    assert response.json()['detail'][0]['type'] == 'extra_forbidden'


def test_rejected_snapshot_still_requires_device_authentication():
    client = browser()
    response = upload(client, 'MOCK_INVALID_DEVICE_TOKEN', {'schema_version': 99})
    assert response.status_code == 401


@pytest.mark.parametrize('malformed_json', [False, True])
def test_malformed_json_and_primitive_errors_do_not_echo_source_values(malformed_json, caplog):
    client = browser()
    _, _, credential = paired(client)
    body = native_sample()
    body['batch_id'] = 'MOCK_PRIVATE_UUID_VALUE'
    with caplog.at_level(logging.WARNING, logger='uvicorn.error'):
        if malformed_json:
            response = client.post('/device/sync',
                headers={'authorization': 'Bearer ' + credential['device_token'], 'content-type': 'application/json'},
                content=b'{"MOCK_PRIVATE_FIELD": MOCK_PRIVATE_INVALID_JSON}')
        else:
            response = upload(client, credential['device_token'], body)
    assert response.status_code == 422
    assert len(response.content) < 4096
    assert 'MOCK_PRIVATE' not in response.text + caplog.text
