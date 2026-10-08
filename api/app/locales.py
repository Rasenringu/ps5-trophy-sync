"""Bounded browser-language matching; never invent publisher translations."""
import re

def choose_language(available: list[str], requested: str, default: str) -> str:
    lookup={language.lower():language for language in available}
    if not isinstance(requested,str):
        requested='en'
    for candidate in requested[:160].split(',')[:8]:
        language=candidate.strip().lower()
        if not re.fullmatch(r'[a-z]{2,3}(?:-[a-z0-9]{2,8})*',language):
            continue
        if language in lookup:
            return lookup[language]
        # Match script before primary language (e.g. zh-Hant-HK vs zh-Hant).
        pieces=language.split('-')
        while len(pieces)>1:
            pieces.pop();short='-'.join(pieces)
            if short in lookup:
                return lookup[short]
        primary=language.split('-')[0]
        alternatives=sorted(k for k in lookup if k.split('-')[0]==primary)
        if alternatives:
            preferred={'en':'en-us','fr':'fr-fr','es':'es-es','pt':'pt-pt','zh':'zh-hans'}.get(primary)
            return lookup[preferred] if preferred in alternatives else lookup[alternatives[0]]
    return lookup.get(default.lower(),lookup.get('en-us',available[0] if available else default))
