"""Optional local private-capture check; no console connection or API upload.

Output includes only the worker's stripped schema-v4 records, never the captured
account/profile fields. All outputs stay in the ignored capture directory.
"""
import json
import struct
import subprocess
import sys
from pathlib import Path

directory=Path('captures/library-investigation/ps4-copy-inspect-v3')
for path in sorted(directory.glob('NPWR*-TRPTITLE.DAT')):
    raw=path.read_bytes()
    identity=struct.unpack_from('>Q',raw,48+32+16)[0]
    profile=struct.unpack_from('>I',raw,identity+16+40)[0]
    title=path.name.split('-')[0]
    result=subprocess.check_output([sys.argv[1],str(path),f'{profile:x}',title],text=True)
    batches=json.loads(result)
    assert all(b['source']=='ps4_bc' and b['schema_version']==4 and not b['mock'] for b in batches)
    rows=[r for b in batches for r in b['trophies']]
    assert len({r['trophy_id'] for r in rows})==len(rows)
    assert all(r['title_id']==title for r in rows)
    assert not any(k in result for k in ['local_user_id','account_id','sealedkey'])
    (directory/(title+'-stripped.json')).write_text(json.dumps(batches))
    print('PASS private PS4 export',title,'records',len(rows))
