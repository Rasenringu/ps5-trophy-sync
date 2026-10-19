"""Resolve PS5 application activity to existing profile-owned trophy identities.

No stored IDs, session counters or trophy records are rewritten. Explicit
publisher bindings take precedence over conservative unique title matching.
PS4 identity remains the separate reader's responsibility.
"""
import json
import re
import unicodedata
from pathlib import Path

VERIFIED_BINDINGS = json.loads(Path(__file__).with_name('native_title_bindings.json').read_text(encoding='utf-8'))


def normalized_title(value):
    if not isinstance(value, str) or not 1 <= len(value) <= 200:
        return None
    # Remove trademark decorations before NFKC turns e.g. TM into title letters.
    text = unicodedata.normalize('NFKC', value.translate(str.maketrans('', '', '™®℠'))).casefold()
    # Keep every word/number and meaningful symbols: N++ must not become N.
    # Punctuation becomes a boundary, never a word concatenation or substring.
    text = ''.join(c if unicodedata.category(c)[0] in 'LNM' or c in '+&#' else ' ' for c in text)
    return ' '.join(text.split()) or None


def native_activity_aliases(records, packages, published_names):
    owned = set()
    exact, normalized = {}, {}

    def add(profile, title, label):
        key = normalized_title(label)
        if not key or label == title:
            return
        exact.setdefault((profile, label), set()).add(title)
        normalized.setdefault((profile, key), set()).add(title)

    for record in records:
        if record.mock or record.source != 'ps5_native' or record.kind != 'trophy':
            continue
        title = record.data['title_id']
        owned.add((record.profile, title))
        add(record.profile, title, record.data['title'])
    for (profile, title), package in packages.items():
        if (profile, title) not in owned or package.metadata_json.get('format') == 'ps4_trp_v3':
            continue
        for texts in package.metadata_json.get('texts', {}).values():
            label = texts.get('', [None])[0]
            add(profile, title, label)
    for profile, title in owned:
        for label in published_names.get(title, ()):
            add(profile, title, label)

    result = {}
    for record in records:
        data = record.data
        if (record.mock or record.source != 'ps5_native' or record.kind != 'activity'
                or data.get('duration_basis') != 'native_foreground_seconds'):
            continue
        application = data.get('native_observation', {}).get('application_title_id', '')
        if not re.fullmatch(r'PPSA[0-9]{5}', application) or data['title_id'] != application:
            continue
        explicit = VERIFIED_BINDINGS.get(application)
        if explicit:
            target = explicit['trophy_set_id']
            if (record.profile, target) in owned:
                result[record.id] = (target, 'verified_native_application_metadata')
            # A known different regional stack must not fall back to a name.
            continue
        if data['title'] == application:
            continue
        candidates = normalized.get((record.profile, normalized_title(data['title'])), set())
        if len(candidates) == 1:
            target = next(iter(candidates))
            basis = ('unique_local_title_metadata' if exact.get((record.profile, data['title'])) == {target}
                     else 'unique_normalized_title_metadata')
            result[record.id] = (target, basis)
    return result
