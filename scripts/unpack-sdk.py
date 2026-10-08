import hashlib, json, pathlib, subprocess, zipfile
archive = pathlib.Path('/tmp/sdk.zip')
lock = json.loads(pathlib.Path('/tmp/toolchain.lock.json').read_text())
if hashlib.sha256(archive.read_bytes()).hexdigest() != lock['ps5_sdk']['sha256']:
    raise SystemExit('SDK checksum mismatch inside Docker build.')
with zipfile.ZipFile(archive) as z:
    for member in z.infolist():
        p = pathlib.PurePosixPath(member.filename)
        if p.is_absolute() or '..' in p.parts:
            raise SystemExit('Unsafe SDK archive path.')
subprocess.run(['unzip', '-q', str(archive), '-d', '/opt'], check=True)
sdk = pathlib.Path('/opt/ps5-payload-sdk')
if not (sdk / 'toolchain/prospero.mk').is_file() or not (sdk / 'samples/hello_world/Makefile').is_file():
    raise SystemExit('SDK layout changed. Inspect upstream before continuing.')
