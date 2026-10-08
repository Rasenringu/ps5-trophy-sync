"""Private fixture serialization test; never contacts console/service/import API."""
import json, subprocess, sys
from pathlib import Path
cli=Path(sys.argv[1]);base=Path('.local/captures/native-format-prefixes')
index=base/'definition-capture-index.json'
if not index.exists():
    print('SKIP private export fixture absent');raise SystemExit(0)
matches=[r for r in json.loads(index.read_text()) if r.get('naruto_reference_match')]
assert len(matches)==1
prefix=Path('.local/console-build/probe-build/private-native-export')
subprocess.run([str(cli),str(base/f"definitions-{matches[0]['capture_index']}.ucp"),str(base/'naruto-state-investigation.dat'),str(prefix)],check=True)
rows=[]
for first in range(0,45,8):
    body=json.loads(Path(f'{prefix}-{first}.json').read_text())
    assert body['schema_version']==2 and body['mock'] is False and body['activities']==[]
    assert body['consistency']=='stable_read_not_atomic'
    assert body['profile_binding']=='foreground_user_path_scoped'
    assert len(Path(f'{prefix}-{first}.json').read_bytes())<=8192
    rows+=body['trophies']
assert len(rows)==45 and sum(t['unlocked'] is True for t in rows)==6
assert sum(t['unlocked'] is False for t in rows)==39
for t in rows:
    assert t['name'] and t['title'] and t['trophy_id'].isdigit()
    if t['unlocked']:
        assert t['grade']=='bronze' and t['clock']=='uncertain' and t['unlocked_at'].endswith('Z')
        assert t['native_observation']['raw_flags']==17
    else:assert t['unlocked_at'] is None and t['clock']=='unknown'
t=json.loads(Path(f'{prefix}-unknown.json').read_text())['trophies'][0]
assert t['unlocked'] is None and t['unlocked_at'] is None and t['clock']=='unknown'
assert t['native_observation']=={'raw_flags':16,'first_raw':'0','second_raw':'62135596800000001'}
print('PASS private DTO export: 45 exact joined records, 6 earned bronze, 39 locked; uncertain times/raw fields retained; MOCK unknown fixture null. No import.')
