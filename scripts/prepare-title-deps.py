"""Pinned public source inputs for local native-title packaging."""
from pathlib import Path
import hashlib
import io
import tarfile
import urllib.request

cache = Path(__file__).resolve().parents[1] / '.local/console-build'
cache.mkdir(parents=True, exist_ok=True)
inputs = [
    ('native-title-source.tar.gz', 'https://codeload.github.com/blackbearreloaded/ps5-native-app-boilerplate/tar.gz/2f672d1c2f508e26f82ce6e27cef289a0861413c',
     'b4d449ec35c30b437b53bc15449ba7e1b1dfcd5778807ac925567c36bd1a1486', 'ps5-native-app-boilerplate-2f672d1c2f508e26f82ce6e27cef289a0861413c'),
    ('zlib-1.3.2.tar.gz', 'https://zlib.net/fossils/zlib-1.3.2.tar.gz',
     'bb329a0a2cd0274d05519d61c667c062e06990d72e125ee2dfa8de64f0119d16', 'zlib-1.3.2'),
]
for filename, url, digest, root in inputs:
    archive = cache / filename
    if not archive.exists():
        with urllib.request.urlopen(url, timeout=60) as response:
            data = response.read(30_000_001)
        if len(data) > 30_000_000 or hashlib.sha256(data).hexdigest() != digest:
            raise SystemExit(f'Archive rejected: {filename}')
        archive.write_bytes(data)
    data = archive.read_bytes()
    if hashlib.sha256(data).hexdigest() != digest:
        raise SystemExit(f'Cached archive rejected: {filename}')
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as tf:
        if any(m.name != root and not m.name.startswith(root + '/') for m in tf.getmembers()):
            raise SystemExit('Unexpected archive root')
        tf.extractall(cache, filter='data')
    print(f'Verified title build input: {filename}, {digest}')
