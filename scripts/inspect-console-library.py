"""Read-only FTP inventory. Personal listings stay in ignored captures/."""
import ftplib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
out = root / 'captures/library-investigation'
out.mkdir(parents=True, exist_ok=True)
host = json.loads((root / 'config/local.json').read_text())['ps5_ip']
ftp = ftplib.FTP()
ftp.connect(host, 2121, timeout=15)
print(ftp.getwelcome())
ftp.login()
inventory = {}

def listing(path):
    try:
        ftp.cwd(path)
        rows = list(ftp.mlsd())
        inventory[path] = rows
        return rows
    except ftplib.error_perm:
        inventory[path] = {'unavailable': True}
        return []

for path in ['/mnt/pfs', '/user/home', '/user/appmeta', '/user/trophy2/nobackup/conf', '/user/trophy/conf', '/system_data/priv/system_logger2/nobackup/database']:
    rows = listing(path)
    print(path if path != '/user/home' else 'Profiles', len(rows), 'entries')
    if path == '/user/home':
        for name, facts in rows:
            if facts.get('type') == 'dir' and len(name) == 8 and all(c in '0123456789abcdefABCDEF' for c in name):
                for suffix in ['trophy2/nobackup/data', 'trophy/data', 'trophy/db']:
                    entries = listing(f'{path}/{name}/{suffix}')
                    print('Profile source', suffix, len(entries), 'entries')
                    if suffix.endswith('/data'):
                        for title, info in entries:
                            if info.get('type') != 'dir' or not title.startswith('NPWR'):
                                continue
                            source = f'{path}/{name}/{suffix}/{title}'
                            files = listing(source)
                            for filename, detail in files:
                                if filename not in ('TRPTITLE.DAT', 'TROPUSR.DAT'):
                                    continue
                                blobs = []
                                for _ in range(2):
                                    parts = []
                                    ftp.retrbinary(f'RETR {source}/{filename}', parts.append)
                                    blobs.append(b''.join(parts))
                                if blobs[0] != blobs[1]:
                                    print('Unstable state skipped', title)
                                    continue
                                dest = out / ('ps5' if suffix.startswith('trophy2') else 'ps4') / title / filename
                                dest.parent.mkdir(parents=True, exist_ok=True)
                                dest.write_bytes(blobs[0])
                                print('Stable state', title, filename, len(blobs[0]), blobs[0][:4].hex())
    if path == '/user/appmeta':
        for name, facts in rows:
            if facts.get('type') != 'dir' or not name.startswith(('PPSA', 'CUSA')):
                continue
            entries = listing(f'{path}/{name}')
            for filename in ['param.json', 'param.sfo']:
                if any(n == filename for n, _ in entries):
                    dest = out / 'appmeta' / name / filename
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    with dest.open('wb') as file:
                        ftp.retrbinary(f'RETR {path}/{name}/{filename}', file.write)
                    if filename == 'param.json':
                        data = json.loads(dest.read_bytes())
                        print(name, data.get('localizedParameters', {}).get('en-US', {}).get('titleName', 'unknown'))
    if path == '/user/trophy2/nobackup/conf':
        for name, facts in rows:
            if facts.get('type') == 'dir' and name.startswith('NPWR'):
                files = listing(f'{path}/{name}')
                if any(n == 'TROPHY.UCP' for n, _ in files):
                    dest = out / 'ps5' / name / 'TROPHY.UCP'
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    with dest.open('wb') as file:
                        ftp.retrbinary(f'RETR {path}/{name}/TROPHY.UCP', file.write)
    if path in ('/user/trophy/conf', '/mnt/pfs'):
        for name, facts in rows:
            if facts.get('type') == 'dir' and name not in ('.', '..'):
                entries = listing(f'{path}/{name}')
                print('PS4/mount inventory', name if path != '/mnt/pfs' else 'trophy mount', [n for n, _ in entries] if path != '/mnt/pfs' else len(entries))
                if path == '/mnt/pfs' and name == 'trophy':
                    for profile, info in entries:
                        if info.get('type') == 'dir' and len(profile) == 8:
                            children = listing(f'{path}/{name}/{profile}')
                            for child, detail in children:
                                if detail.get('type') == 'dir' and child not in ('.', '..'):
                                    files = listing(f'{path}/{name}/{profile}/{child}')
                                    print('Mounted PS4 source', child, [n for n, _ in files])
                                    for sub, details in files:
                                        if details.get('type') == 'dir' and sub not in ('.', '..'):
                                            nested = listing(f'{path}/{name}/{profile}/{child}/{sub}')
                                            print('Mounted PS4 contents', sub, [n for n, _ in nested])
(out / 'inventory.json').write_text(json.dumps(inventory, indent=2))
ftp.quit()
print('Private inventory saved under ignored captures/library-investigation; no database copied.')
