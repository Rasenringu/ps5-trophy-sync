"""Run only the specifically authorized library diagnostic; never auto-build.

Requires explicit authorization per AGENTS.md. This is not a sync/deploy helper.
"""
import ftplib
import json
import re
import time
import urllib.request
from pathlib import Path

root = Path(__file__).resolve().parents[1]
config = json.loads((root / 'config/local.json').read_text())
binary = root / 'artifacts/console/library-diagnostic/LibraryDiagnostic.elf'
report = '/data/trophy-sync-library-report.txt'
ftp = ftplib.FTP()
ftp.connect(config['ps5_ip'], 2121, timeout=15)
ftp.login()
ftp.cwd('/data')
if any(name == report.rsplit('/', 1)[1] for name, _ in ftp.mlsd()):
    raise SystemExit('A diagnostic report already exists; no payload sent or file overwritten.')
manager = 'http://' + config['ps5_ip'] + ':8084'
version = urllib.request.urlopen(manager + '/version', timeout=5).read().decode().strip()
if version != '0.5.2':
    raise SystemExit('Unsupported manager version; no payload uploaded or run.')
stage = '/data/pldmgr/payloads/library-investigation'
ftp.cwd('/data/pldmgr/payloads')
if any(name == 'library-investigation' for name, _ in ftp.mlsd()):
    raise SystemExit('Diagnostic staging directory already exists; no overwrite or execution.')
ftp.mkd(stage)
with binary.open('rb') as file:
    ftp.storbinary('STOR ' + stage + '/LibraryDiagnostic.elf', file)
response = urllib.request.urlopen(manager + '/loadpayload:' + stage + '/LibraryDiagnostic.elf', timeout=15).read().decode().strip()
print('Authorized one-shot diagnostic launch response:', response)
out = root / 'captures/library-investigation'
out.mkdir(parents=True, exist_ok=True)
for _ in range(30):
    parts = []
    try:
        ftp.retrbinary('RETR ' + report, parts.append)
    except ftplib.error_perm:
        time.sleep(1)
        continue
    body = b''.join(parts)
    if body and b'PS4 mounted trophy db:' in body:
        text = re.sub(r'(table=\w+)_\d{8,10}\b', r'\1_<profile>', body.decode('utf-8', errors='replace'))
        (out / 'library-report.txt').write_text(text, encoding='utf-8')
        print(text)
        break
    time.sleep(1)
else:
    raise SystemExit('No diagnostic report received; do not infer a successful console result.')
ftp.quit()
