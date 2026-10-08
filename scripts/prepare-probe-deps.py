"""Pinned source archives for read-only console reader and HTTPS transport, outside the SDK."""
import hashlib
import io
import tarfile
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
cache = ROOT/'.local/console-build'
cache.mkdir(parents=True, exist_ok=True)
sources = [
    ('mbedtls-3.6.7.tar.bz2', 'https://github.com/Mbed-TLS/mbedtls/releases/download/mbedtls-3.6.7/mbedtls-3.6.7.tar.bz2',
     'a7e8bcbec0e6f761b4af24f25677626b35f762f68eef79c08677a363212d11f6', 'mbedtls-3.6.7'),
    ('sqlite-amalgamation-3530400.zip', 'https://www.sqlite.org/2026/sqlite-amalgamation-3530400.zip',
     '1e71ddf93849c6a6ecf58b827c0692073d2dd7ee40196158068f7b29f422e87d', 'sqlite-amalgamation-3530400'),
]
for filename, url, digest, prefix in sources:
    archive = cache/filename
    if not archive.exists():
        with urllib.request.urlopen(url, timeout=45) as response:
            data = response.read(20_000_001)
        if len(data) > 20_000_000 or hashlib.sha256(data).hexdigest() != digest:
            raise SystemExit('Downloaded source rejected: '+filename)
        archive.write_bytes(data)
    data = archive.read_bytes()
    if hashlib.sha256(data).hexdigest() != digest:
        raise SystemExit('Cached source rejected: '+filename)
    if filename.endswith('.zip'):
        with zipfile.ZipFile(io.BytesIO(data)) as source:
            for name in source.namelist():
                if not name.startswith(prefix+'/') or '..' in Path(name).parts or '\\' in name:
                    raise SystemExit('Unsafe SQLite archive')
            source.extractall(cache)
    else:
        with tarfile.open(fileobj=io.BytesIO(data), mode='r:bz2') as source:
            if any(m.name != prefix and not m.name.startswith(prefix+'/') for m in source.getmembers()):
                raise SystemExit('Unexpected TLS archive root')
            source.extractall(cache, filter='data')
    print('Verified console dependency:', filename, digest)
