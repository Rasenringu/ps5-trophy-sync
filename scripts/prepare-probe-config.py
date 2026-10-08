"""Generate ignored console endpoint/public CA header. Contains no secret."""
import json
import os
import hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
mode=os.environ.get('TROPHY_SYNC_ENDPOINT','public')
if mode=='public':
    endpoint=json.loads((ROOT/'config/public-service.json').read_text())
    identity={'server_ip':endpoint['host'],'port':endpoint['port'],'origin':endpoint['origin']}
    data=(ROOT/endpoint['ca_file']).read_bytes()
    if hashlib.sha256(data).hexdigest()!=endpoint['ca_sha256']:
        raise SystemExit('Public CA bundle checksum mismatch')
    ca=data.decode('ascii')
    state='/data/trophy-sync-party'
elif mode=='lan':
    identity=json.loads((ROOT/'.local/tls/identity.json').read_text())
    config=json.loads((ROOT/'config/local.json').read_text(encoding='utf-8-sig'))
    if identity['origin'] != config['service_url']:
        raise SystemExit('TLS identity and configured service differ')
    ca=(ROOT/'.local/tls/ca.crt').read_text(encoding='ascii')
    state='/data/trophy-sync-worker'
else:
    raise SystemExit('TROPHY_SYNC_ENDPOINT must be public or lan')
out=ROOT/'.local/console-build/probe-config';out.mkdir(parents=True,exist_ok=True)
(out/'probe_config.h').write_text(
    '#pragma once\n#define PROBE_IP '+json.dumps(identity['server_ip'])+
    '\n#define PROBE_PORT '+str(identity['port'])+'\n#define PROBE_CA '+json.dumps(ca)+
    '\n#define PROBE_ORIGIN '+json.dumps(identity['origin'])+
    '\n#define PROBE_STATE_DIRECTORY '+json.dumps(state)+'\n',encoding='ascii')
(out/'endpoint.json').write_text(json.dumps({'origin':identity['origin'],'ca_sha256':hashlib.sha256(ca.encode()).hexdigest()},indent=2)+'\n')
print('Generated console config for '+identity['origin']+'; no credentials included.')
