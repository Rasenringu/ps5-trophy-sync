"""Package current source builds, with notices, without consuming previous releases."""
from pathlib import Path
import hashlib
import json
import zipfile
root = Path(__file__).resolve().parents[1]
base = root / 'artifacts/console/final-ui'
title = base / 'PPSA99889'
worker = base / 'TrophySync.elf'
if not worker.is_file():
    raise SystemExit('Build TrophySync.elf first with scripts/Build-Console.ps1')
metadata = json.loads((root / 'console/ui/param.json').read_text())
assert metadata['titleId'] == title.name
(title / 'sce_sys/param.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
licenses = title / 'licenses'
licenses.mkdir(exist_ok=True)
notices = {
    'GPL-3.0.txt': 'console/COPYING',
    'MbedTLS.txt': 'console/vendor/MBEDTLS-LICENSE.txt',
    'NotoSansDisplay-OFL.txt': 'console/vendor/noto-sans-display/OFL.txt',
    'Nayuki.txt': 'console/vendor/qrcodegen.c',
    'Native-runtime.txt': '.local/console-build/ps5-native-app-boilerplate-2f672d1c2f508e26f82ce6e27cef289a0861413c/LICENSE',
    'SQLite-public-domain.txt': '.local/console-build/sqlite-amalgamation-3530400/sqlite3.c',
    'zlib.txt': '.local/console-build/zlib-1.3.2/LICENSE',
}
for name, source in notices.items():
    data = (root / source).read_bytes()
    if name == 'Nayuki.txt': data = data[:data.index(b'#include')]
    if name == 'SQLite-public-domain.txt':
        start = data.index(b'May you do good and not evil.')
        data = data[max(0, data.rfind(b'/*', 0, start)):data.index(b'*/', start) + 2] + b'\n'
    (licenses / name).write_bytes(data)
(licenses / 'PROVENANCE.txt').write_text(
    'TrophySync console: GPL-3.0-or-later. See corresponding source/build inputs in the monorepo.\n'
    'SDK v0.43; source commit d9c9519116944a7f1c22d262012c53b80b3520b7.\n'
    'Native startup/runtime/tooling and tiled frame adaptation: BlackBearReloaded, GPL-3.0-or-later, '
    'commit 2f672d1c2f508e26f82ce6e27cef289a0861413c; tooling credits SvenGDK/SharpProspero.\n'
    'Worker links Mbed TLS 3.6.7 (Apache-2.0 option) and SQLite 3.53.4 (public domain).\n'
    'QR generator: Nayuki, MIT. Noto Sans Display: Google, OFL-1.1. Host tooling uses zlib 1.3.2.\n'
    'No proprietary runtime module is copied. Distribution requires corresponding GPL source.\n', encoding='utf-8')
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
title_files = [title / p for p in ['eboot.bin', 'sce_module/libc.prx', 'sce_sys/param.json', 'sce_sys/icon0.png']]
title_files += [licenses / p for p in [*notices, 'PROVENANCE.txt']]
sources = [p for p in (root / 'console').rglob('*') if p.is_file() and 'build' not in p.parts and '__pycache__' not in p.parts]
sources += [p for p in (root / 'scripts').iterdir() if p.is_file() and ('build' in p.name.lower() or 'prepare' in p.name or 'generate-console' in p.name or p.name == 'package-final-ui.py')]
sources += [root / 'toolchain.lock.json', root / 'docs/upstream.lock.json', root / 'config/public-service.json']
manifest = {'title_id': title.name, 'content_version': metadata['contentVersion'], 'console_verified': False,
    'endpoint': json.loads((root / '.local/console-build/probe-config/endpoint.json').read_text()),
    'worker_filename': worker.name, 'worker_sha256': sha(worker), 'passive_sync': False,
    'files': {p.relative_to(title).as_posix(): sha(p) for p in sorted(title_files)},
    'source_sha256': {p.relative_to(root).as_posix(): sha(p) for p in sorted(sources)},
    'font': json.loads((root / 'console/vendor/noto-sans-display/source.json').read_text())}
(base / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
(base / 'INSTALL.txt').write_text(
    'TrophySync service: ' + manifest['endpoint']['origin'] + '\n'
    'Install BOTH TrophySync.elf in Payload Manager and PPSA99889 via ShadowMount.\n'
    'ELF alone requires foreground title IPC; do not enable standalone autoload.\n'
    'Register/sign in on the service, open TrophySync, scan QR/enter code at /pair.\n'
    'Confirm the displayed console/profile. Each installation pairs separately.\n'
    'Native PS5 trophies/recorded playtime only. PS4/passive sync unsupported.\n'
    'FW 8.00 baseline; other firmware/loader configurations unverified.\n'
    'This public-service build has not been validated on a PS5.\n'
    'GPL distribution requires corresponding source; retain licenses.\n', encoding='utf-8')
with zipfile.ZipFile(base / 'TrophySync-PS5.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
    for p in sorted(title_files):
        archive.write(p, p.relative_to(base).as_posix())
    for p in [worker, base / 'manifest.json', base / 'INSTALL.txt']: archive.write(p, p.name)
print('Packaged current TrophySync sources; no historical release input.')
print('Worker SHA256:', manifest['worker_sha256'])
print('Foreground SHA256:', manifest['files']['eboot.bin'])
