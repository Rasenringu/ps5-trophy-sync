"""Read-only queue acknowledgement evidence; never reads connection credentials.

Copies no raw files. Summaries omit profile/device/batch IDs and source timestamps.
Queue slots are reusable, so this cannot establish the whole server library.
"""
import ftplib
import hashlib
import json
import re
import struct
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

root = Path(__file__).resolve().parents[1]
host = json.loads((root / 'config/local.json').read_text())['ps5_ip']
ftp = ftplib.FTP()
ftp.connect(host, 2121, timeout=10)
ftp.login()
ftp.cwd('/data/trophy-sync-party')
names = [name for name, facts in ftp.mlsd()
         if facts.get('type') == 'file' and re.fullmatch(r'queue-[0-9a-f]{8}-[0-9]{2}\.bin', name)]
ack = Counter()
kinds = Counter()
sources = Counter()
requested = {}
unstable = 0

def read(name):
    chunks = []
    size = 0
    def receive(chunk):
        nonlocal size
        size += len(chunk)
        if size > 8516:
            raise ValueError('Queue file exceeds known format bound')
        chunks.append(chunk)
    ftp.retrbinary('RETR ' + name, receive)
    return b''.join(chunks)

for name in names:
    body = read(name)
    if body != read(name):
        unstable += 1
        continue
    if len(body) != 8516 or body[:8] != b'PS5Q2\0\0\0':
        raise ValueError('Unsupported queue structure')
    version, acknowledged, profile, length = struct.unpack_from('<IIII', body, 8)
    if version != 2 or acknowledged not in (0, 1) or not 1 <= length <= 8192:
        raise ValueError('Invalid queue fields')
    sealed = bytearray(body)
    sealed[290:322] = bytes(32)
    if hashlib.sha256(sealed).digest() != body[290:322]:
        raise ValueError('Invalid queue digest')
    snapshot = json.loads(body[322:322+length])
    if snapshot.get('mock') is not False or snapshot.get('source') not in ('ps5_native','ps4_bc'):
        raise ValueError('Queue evidence is not a real console observation')
    if snapshot['source']=='ps4_bc' and snapshot.get('schema_version')!=4:
        raise ValueError('Unsupported PS4 queue evidence')
    sources[snapshot['source']] += 1
    ack[acknowledged] += 1
    for kind in ('trophies', 'activities'):
        for row in snapshot[kind]:
            kinds[kind] += 1
            if row['title_id'] not in ('PPSA74207', 'PPSA99902', 'CUSA03804', 'CUSA02344', 'NPWR26589_00','NPWR09798_00','NPWR09799_00','NPWR09801_00','NPWR10954_00','NPWR29343_00'):
                continue
            entry = requested.setdefault(row['title_id'], {'title': row['title'], 'trophies': 0,
                'activities': 0, 'acknowledged_records': 0, 'completed_seconds': 0, 'earned': 0, 'locked': 0, 'unknown': 0})
            entry[kind] += 1
            entry['acknowledged_records'] += acknowledged
            if kind=='trophies':
                entry['earned' if row.get('unlocked') is True else 'locked' if row.get('unlocked') is False else 'unknown'] += 1
            if kind == 'activities' and row.get('complete') and row.get('duration_seconds') is not None:
                entry['completed_seconds'] += row['duration_seconds']
ftp.quit()
report = {'scope': 'Stable surviving queue slots only; slots are reused after acknowledgement',
    'acknowledged_slots': ack[1], 'pending_slots': ack[0], 'unstable_slots_skipped': unstable,
    'records': dict(kinds), 'source_slots':dict(sources), 'requested_games': requested}
destination = root / 'captures/library-investigation/queue-summary.json'
destination.parent.mkdir(parents=True, exist_ok=True)
destination.write_text(json.dumps(report, indent=2), encoding='utf-8')
stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
(destination.parent / ('queue-summary-' + stamp + '.json')).write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report, indent=2))
