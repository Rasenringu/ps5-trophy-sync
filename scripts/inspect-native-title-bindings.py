"""Read-only PS5 publisher bindings; no DB, credentials or payload access.

The native trophy2 path and this 532-byte single-set format were independently
observed on two PS5 releases. Do not infer PS5 support from a PS4 filename/path.
Raw publisher metadata stays in ignored captures/; only IDs/hashes are printed.
"""
import argparse
import ftplib
import hashlib
import json
import re
import struct
from pathlib import Path


def binding(raw):
    if len(raw) != 532:
        raise ValueError('Unsupported native binding size; inspect new format independently')
    if (struct.unpack_from('>IIQQQ', raw) != (0xd294a018, 1, len(raw), 384, 1)
            or any(raw[32:128]) or hashlib.sha1(raw[:-20]).digest() != raw[-20:]):
        raise ValueError('Native binding header/digest mismatch')
    cursor = 128
    for tag, length in ((0x10, 12), (0x11, 12), (0x12, 176), (0x13, 16)):
        if struct.unpack_from('>HH', raw, cursor) != (tag, length):
            raise ValueError('Unsupported native binding entry')
        cursor += 4 + length
    if any(raw[cursor:-20]):
        raise ValueError('Unsupported native binding padding')
    title = raw[132:144].decode('ascii')
    if not re.fullmatch(r'NPWR[0-9]{5}_00', title):
        raise ValueError('Invalid native trophy-set identity')
    return title


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate publisher metadata field')
        result[key] = value
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('applications', nargs='+', help='Exact PPSA application IDs')
    apps = parser.parse_args().applications
    if any(not re.fullmatch(r'PPSA[0-9]{5}', app) for app in apps):
        raise ValueError('Invalid PS5 application ID')
    root = Path(__file__).resolve().parents[1]
    host = json.loads((root / 'config/local.json').read_text())['ps5_ip']
    report = {}
    with ftplib.FTP() as ftp:
        ftp.connect(host, 2121, timeout=15)
        ftp.login()
        for app in apps:
            folder = root / 'captures/library-investigation/native-bindings' / app
            folder.mkdir(parents=True, exist_ok=True)
            raw_files = {}
            for name in ('param.json', 'trophy2/npbind.dat'):
                copies = []
                for _ in range(2):
                    parts = []
                    total = 0

                    def receive(part):
                        nonlocal total
                        total += len(part)
                        if total > 1024 * 1024:
                            raise ValueError('Native publisher metadata exceeds bounds')
                        parts.append(part)

                    ftp.retrbinary(f'RETR /system_data/priv/appmeta/{app}/{name}', receive)
                    copies.append(b''.join(parts))
                if copies[0] != copies[1]:
                    raise ValueError('Native publisher metadata changed during read')
                raw_files[name] = copies[0]
                (folder / name.replace('/', '-')).write_bytes(copies[0])
            param = json.loads(raw_files['param.json'], object_pairs_hook=unique)
            if (param.get('titleId') != app
                    or not re.fullmatch(r'[A-Z]{2}[0-9]{4}-' + app + r'_[0-9]{2}-[A-Z0-9]{16}', param.get('contentId', ''))):
                raise ValueError('Native application metadata identity mismatch')
            report[app] = {'trophy_set_id': binding(raw_files['trophy2/npbind.dat']), 'evidence': {
                'source': f'/system_data/priv/appmeta/{app}/trophy2/npbind.dat',
                'content_id': param['contentId'],
                'param_json_sha256': hashlib.sha256(raw_files['param.json']).hexdigest(),
                'npbind_sha256': hashlib.sha256(raw_files['trophy2/npbind.dat']).hexdigest(),
                'npbind_bytes': len(raw_files['trophy2/npbind.dat']), 'npbind_entries': 1,
                'npbind_trailing_sha1_verified': True, 'consistency': 'two_equal_bounded_reads'}}
            (folder / 'summary.json').write_text(json.dumps(report[app], indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
