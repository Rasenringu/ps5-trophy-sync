"""Bounded artwork reader for the observed native UCP format (not unlock state)."""
import hashlib
import json
import re
import struct
import zlib

def png(data: bytes) -> bytes:
    if not 45 <= len(data) <= 2 * 1024 * 1024 or data[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('Invalid or oversized PNG')
    offset, seen, image = 8, set(), False
    while offset < len(data):
        if offset + 12 > len(data):
            raise ValueError('Truncated PNG')
        length = struct.unpack_from('>I', data, offset)[0]
        kind = data[offset+4:offset+8]
        end = offset + 12 + length
        if end > len(data) or zlib.crc32(data[offset+4:end-4]) & 0xffffffff != struct.unpack_from('>I', data, end-4)[0]:
            raise ValueError('Invalid PNG bounds/checksum')
        if not seen and kind != b'IHDR':
            raise ValueError('Missing PNG header')
        if kind == b'IHDR':
            if seen or length != 13:
                raise ValueError('Invalid PNG header')
            width, height, depth, color, compression, filtering, interlace = struct.unpack('>IIBBBBB', data[offset+8:end-4])
            allowed = {0: (1,2,4,8,16), 2: (8,16), 3: (1,2,4,8), 4: (8,16), 6: (8,16)}
            if not 1 <= width <= 2048 or not 1 <= height <= 2048 or depth not in allowed.get(color, ()) or compression or filtering or interlace not in (0,1):
                raise ValueError('Unsupported PNG dimensions/format')
        if kind in (b'acTL', b'fcTL', b'fdAT'):
            raise ValueError('Animated artwork unsupported')
        image |= kind == b'IDAT'
        seen.add(kind)
        offset = end
        if kind == b'IEND':
            if length or offset != len(data) or not image:
                raise ValueError('Invalid PNG end')
            return data
    raise ValueError('Missing PNG end')

def entries(data: bytes) -> dict[str, bytes]:
    if not 96 <= len(data) <= 64 * 1024 * 1024:
        raise ValueError('UCP size outside bounds')
    magic, version, size, count, stride = struct.unpack_from('>IIQII', data)
    if (magic, version, size, stride) != (0xb228c60a, 1, len(data), 64) or not 1 <= count <= 4096 or 96+count*64 > size:
        raise ValueError('Unsupported UCP header')
    if hashlib.sha1(data[:28]+bytes(20)+data[48:]).digest() != data[28:48]:
        raise ValueError('UCP integrity mismatch')
    result, ranges = {}, []
    for i in range(count):
        offset = 96+i*64
        raw = data[offset:offset+32]
        name = raw.split(b'\0', 1)[0].decode('ascii')
        if not name or name in ('.','..') or any(ord(c)<32 or ord(c)>126 or c in '/\\' for c in name) or raw != name.encode().ljust(32,b'\0') or name in result:
            raise ValueError('Unsafe/duplicate UCP entry')
        start, length = struct.unpack_from('>QQ', data, offset+32)
        if start < 96+count*64 or start+length > size:
            raise ValueError('UCP entry outside bounds')
        result[name] = data[start:start+length]
        if length:
            ranges.append((start,start+length))
    ranges.sort()
    if any(a[1]>b[0] for a,b in zip(ranges,ranges[1:])):
        raise ValueError('Overlapping UCP entries')
    return result

def read_artwork(data: bytes) -> tuple[str, dict[str, bytes]]:
    files = entries(data)
    def unique(pairs):
        out = {}
        for key, value in pairs:
            if key in out:
                raise ValueError('Duplicate metadata key')
            out[key] = value
        return out
    if len(files['tropconf.json']) > 1024*1024:
        raise ValueError('Oversized trophy metadata')
    conf = json.loads(files['tropconf.json'], object_pairs_hook=unique)
    title = conf['trophyNpCommId']
    if not re.fullmatch(r'NPWR[0-9]{5}_00', title) or conf.get('schemaVersion') not in ('0.90','1.00') or 'PS5' not in conf.get('platform',[]):
        raise ValueError('Unsupported native trophy identity')
    images = {}
    ids = [t['id'] for t in conf['trophies']]
    if len(ids)>1000 or len(set(ids))!=len(ids) or any(not isinstance(i,str) or not re.fullmatch(r'[0-9]{1,8}',i) for i in ids):
        raise ValueError('Invalid trophy identifiers')
    for trophy in ids:
        name = f'trop{int(trophy):04d}.png'
        if name in files:
            images[trophy] = png(files[name])
    language = conf.get('defaultLanguage','en-US')
    for name in (f'icon0_{language}.png','icon0_en-US.png','icon0.png'):
        if name in files:
            images[''] = png(files[name])
            break
    return title, images

def read_trophy_info(data: bytes) -> tuple[str, dict[str, tuple[bool, str]]]:
    files = entries(data)
    def unique(pairs):
        result = {}
        for key,value in pairs:
            if key in result:
                raise ValueError('Duplicate metadata key')
            result[key] = value
        return result
    conf = json.loads(files['tropconf.json'],object_pairs_hook=unique)
    language = conf['defaultLanguage']
    if not isinstance(language,str) or not re.fullmatch(r'[A-Za-z0-9-]{1,15}',language):
        raise ValueError('Invalid metadata language')
    raw = files['tropmeta_'+language+'.json']
    if len(raw)>1024*1024:
        raise ValueError('Oversized trophy descriptions')
    meta = json.loads(raw,object_pairs_hook=unique)
    for key in ('trophyNpCommId','trophyDefinitionRevision','trophySetVersion'):
        if meta.get(key) != conf.get(key):
            raise ValueError('Metadata identity/revision mismatch')
    if meta.get('schemaVersion') != '0.90':
        raise ValueError('Unsupported trophy metadata')
    descriptions = {}
    for item in meta['metadata']['trophyMetadata']:
        if item['id'] in descriptions or not isinstance(item.get('detail'),str) or len(item['detail'])>4000:
            raise ValueError('Invalid/duplicate description')
        descriptions[item['id']] = item['detail']
    result = {}
    for item in conf['trophies']:
        if not isinstance(item.get('hidden'),bool) or item['id'] not in descriptions or item['id'] in result:
            raise ValueError('Invalid secret flag/metadata join')
        result[item['id']] = (item['hidden'], descriptions[item['id']])
    if result.keys()!=descriptions.keys():
        raise ValueError('Incomplete trophy metadata join')
    return conf['trophyNpCommId'],result

def read_localized_text(data: bytes) -> tuple[str, dict[str, dict[str, tuple[str,str]]], str]:
    files=entries(data)
    def unique(pairs):
        result={}
        for key,value in pairs:
            if key in result:
                raise ValueError('Duplicate localized metadata key')
            result[key]=value
        return result
    conf=json.loads(files['tropconf.json'],object_pairs_hook=unique)
    ids={item['id'] for item in conf['trophies']}
    result={}
    for name,raw in files.items():
        match=re.fullmatch(r'tropmeta_([A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*)\.json',name)
        if not match:
            continue
        language=match[1]
        if len(language)>15 or len(raw)>1024*1024:
            raise ValueError('Oversized localized metadata')
        meta=json.loads(raw,object_pairs_hook=unique)
        if meta.get('schemaVersion')!='0.90' or any(meta.get(k)!=conf.get(k) for k in ('trophyNpCommId','trophyDefinitionRevision','trophySetVersion')):
            raise ValueError('Localized identity/revision mismatch')
        title=meta['metadata']['titleMetadata']['name']
        if not isinstance(title,str) or not 1<=len(title)<=200:
            raise ValueError('Invalid localized title')
        rows={'':(title,'')}
        for item in meta['metadata']['trophyMetadata']:
            trophy=item['id'];label=item.get('name');detail=item.get('detail')
            if trophy not in ids or trophy in rows or not isinstance(label,str) or not 1<=len(label)<=200 or not isinstance(detail,str) or len(detail)>4000:
                raise ValueError('Invalid localized trophy join')
            rows[trophy]=(label,detail)
        if set(rows)-{''}!=ids or language.lower() in {k.lower() for k in result}:
            raise ValueError('Incomplete/duplicate language')
        result[language]=rows
    if conf['defaultLanguage'] not in result:
        raise ValueError('Default translation missing')
    return conf['trophyNpCommId'],result,conf['defaultLanguage']
