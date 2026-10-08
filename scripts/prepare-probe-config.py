"""Generate ignored console endpoint/public CA header. Contains no secret."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
identity=json.loads((ROOT/'.local/tls/identity.json').read_text())
config=json.loads((ROOT/'config/local.json').read_text(encoding='utf-8-sig'))
if identity['origin'] != config['service_url']:
    raise SystemExit('TLS identity and configured service differ')
ca=(ROOT/'.local/tls/ca.crt').read_text(encoding='ascii')
out=ROOT/'.local/console-build/probe-config';out.mkdir(parents=True,exist_ok=True)
(out/'probe_config.h').write_text(
    '#pragma once\n#define PROBE_IP '+json.dumps(identity['server_ip'])+
    '\n#define PROBE_PORT '+str(identity['port'])+'\n#define PROBE_CA '+json.dumps(ca)+'\n',encoding='ascii')
print('Generated local public-CA console config; no credentials included.')
