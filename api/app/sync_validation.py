"""Bounded sync diagnostics, without echoing private source data or credentials."""
import hashlib
import logging
from pathlib import Path

from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .contracts import Snapshot, NativeSnapshot, NativeActivitySnapshot, Ps4Snapshot


MODELS = (Snapshot, NativeSnapshot, NativeActivitySnapshot, Ps4Snapshot)
FIELDS = {'body'}
for model in MODELS:
    schema = model.model_json_schema()
    for definition in (schema, *schema.get('$defs', {}).values()):
        FIELDS.update(definition.get('properties', {}))

# Compare running hosts without exposing source, environment or account data.
_directory = Path(__file__).parent
SYNC_VALIDATOR_SHA256 = hashlib.sha256(b''.join(
    (_directory / name).read_bytes().replace(b'\r\n', b'\n')
    for name in ('main.py', 'contracts.py', 'observation_times.py', 'sync_validation.py')
)).hexdigest()


async def validation_error(request, exc: RequestValidationError):
    if request.url.path != '/device/sync':
        return await request_validation_exception_handler(request, exc)
    errors = exc.errors()
    version = exc.body.get('schema_version') if isinstance(exc.body, dict) else None
    version = version if type(version) is int and version in (1, 2, 3, 4) else None
    detail = []
    for error in errors[:6]:
        # Extra-field names and invalid discriminator messages can contain input.
        location = [part if type(part) is int or part in FIELDS else 'field'
                    for part in error['loc'][:8]]
        kind = error['type']
        # Our model validators raise fixed messages. Primitive/discriminator
        # errors may quote submitted values, so use fixed summaries for those.
        message = error['msg'] if kind in ('value_error', 'literal_error', 'string_pattern_mismatch') else {
            'union_tag_invalid': 'Unsupported schema_version; update the serving API and worker together',
            'union_tag_not_found': 'schema_version is required',
            'json_invalid': 'Invalid snapshot JSON',
        }.get(kind, 'Invalid field value')
        detail.append({'loc': location, 'type': kind, 'msg': message[:160]})
    # These are sanitized field paths and validator messages only. Never log
    # the exception/body repr, input/context, submitted IDs or tokens.
    logging.getLogger('uvicorn.error').warning(
        'Sync validation rejected: schema_version=%s errors=%d fields=%s',
        version, len(errors), detail)
    return JSONResponse({'code': 'invalid_snapshot', 'schema_version': version,
                         'detail': detail, 'errors_truncated': len(errors) > len(detail)},
                        status_code=422)
