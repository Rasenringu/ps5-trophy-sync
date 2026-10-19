"""Read-only publisher metadata evidence. No database, credentials or payload.

FTPSRV 0.21.1 ignores MLSD path arguments; RETR uses explicit absolute paths.
Raw publisher files stay in ignored captures/. Only a redacted summary is printed.
"""
import argparse
import ftplib
import hashlib
import json
import re
import struct
from pathlib import Path


def npbind(raw):
    if not 148 <= len(raw) <= 128 + 128 * 384 + 20:
        raise ValueError('npbind size outside bounds')
    magic, version, size, stride, count = struct.unpack_from('>IIQQQ', raw)
    if ((magic, version, size, stride) != (0xd294a018, 1, len(raw), 384)
            or not 1 <= count <= 128 or len(raw) != 128 + count * stride + 20
            or any(raw[32:128]) or hashlib.sha1(raw[:-20]).digest() != raw[-20:]):
        raise ValueError('Unsupported or inconsistent npbind header/digest')
    titles = []
    for index in range(count):
        entry = raw[128 + index * stride:128 + (index + 1) * stride]
        cursor = 0
        for tag, length in ((0x10, 12), (0x11, 12), (0x12, 176), (0x13, 16)):
            if struct.unpack_from('>HH', entry, cursor) != (tag, length):
                raise ValueError('Unsupported npbind entry')
            if tag == 0x10:
                title = entry[cursor + 4:cursor + 4 + length].decode('ascii')
                if not re.fullmatch(r'NPWR[0-9]{5}_00', title) or title in titles:
                    raise ValueError('Invalid/duplicate npbind identity')
                titles.append(title)
            cursor += 4 + length
        if any(entry[cursor:]):
            raise ValueError('Unsupported npbind padding')
    return titles


def sfo(raw):
    if not 20 <= len(raw) <= 65536:
        raise ValueError('SFO size outside bounds')
    magic, version, keys, data, count = struct.unpack_from('<IIIII', raw)
    if (magic, version) != (0x46535000, 0x101) or not 1 <= count <= 256 or not 20 + count * 16 <= keys < data <= len(raw):
        raise ValueError('Unsupported SFO header')
    fields = {}
    for index in range(count):
        key_offset, fmt, length, capacity, value_offset = struct.unpack_from('<HHIII', raw, 20 + index * 16)
        start = keys + key_offset
        if not keys <= start < data or not length <= capacity or data + value_offset + capacity > len(raw):
            raise ValueError('SFO entry outside bounds')
        end = raw.find(b'\0', start, data)
        if end < 0:
            raise ValueError('Unterminated SFO key')
        key = raw[start:end].decode('ascii')
        if key in fields:
            raise ValueError('Duplicate SFO key')
        value = raw[data + value_offset:data + value_offset + length]
        fields[key] = value.rstrip(b'\0').decode('utf-8') if fmt == 0x204 else None
    return fields


def main():
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument('application', help='Exact CUSA application ID, e.g. CUSA02344')
    application = args.parse_args().application
    if not re.fullmatch(r'CUSA[0-9]{5}', application):
        raise ValueError('Invalid PS4 application ID')
    root = Path(__file__).resolve().parents[1]
    host = json.loads((root / 'config/local.json').read_text())['ps5_ip']
    folder = root / 'captures/library-investigation/ps4-collections' / application
    folder.mkdir(parents=True, exist_ok=True)
    raw_files = {}
    with ftplib.FTP() as ftp:
        ftp.connect(host, 2121, timeout=15)
        ftp.login()
        for name in ('npbind.dat', 'param.sfo'):
            copies = []
            for _ in range(2):
                parts = []
                total = 0

                def receive(chunk):
                    nonlocal total
                    total += len(chunk)
                    if total > 65536:
                        raise ValueError('Publisher metadata exceeds bounds')
                    parts.append(chunk)

                ftp.retrbinary(f'RETR /system_data/priv/appmeta/{application}/{name}', receive)
                copies.append(b''.join(parts))
            if copies[0] != copies[1]:
                raise ValueError('Publisher metadata changed during read')
            raw_files[name] = copies[0]
            (folder / name).write_bytes(copies[0])
    fields = sfo(raw_files['param.sfo'])
    if fields.get('TITLE_ID') != application or not re.fullmatch(r'[A-Z]{2}[0-9]{4}-' + application + r'_[0-9]{2}-[A-Z0-9]{16}', fields.get('CONTENT_ID') or ''):
        raise ValueError('Application metadata identity mismatch')
    report = {'application_title_id': application, 'title': fields.get('TITLE'),
              'application_version': fields.get('APP_VER'), 'content_id': fields.get('CONTENT_ID'),
              'trophy_sets': npbind(raw_files['npbind.dat']),
              'npbind_bytes': len(raw_files['npbind.dat']),
              'npbind_sha256': hashlib.sha256(raw_files['npbind.dat']).hexdigest(),
              'param_sfo_sha256': hashlib.sha256(raw_files['param.sfo']).hexdigest(),
              'consistency': 'two_equal_bounded_reads', 'npbind_trailing_sha1_verified': True}
    (folder / 'summary.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()
