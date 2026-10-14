"""Observed PS4 TRP v3 definitions/images, independent of profile unlock state."""
import hashlib
import re
import struct
from xml.etree import ElementTree as ET
from Cryptodome.Cipher import AES
from .console_artwork import png

# Public PS4 ESFM format constant, published by independent TRP readers.
# It is common to packages, not a device credential, sealed key or user secret.
_FORMAT_KEY=bytes.fromhex('21f41a6bad8a1d3eca7ad586c101b7a9')
_GRADES={'P':'platinum','G':'gold','S':'silver','B':'bronze'}
_LANGUAGES={0:'ja-JP',1:'en-US',2:'fr-FR',3:'es-ES',4:'de-DE',5:'it-IT',
            6:'nl-NL',7:'pt-PT',8:'ru-RU',9:'ko-KR',10:'zh-TW',11:'zh-CN',
            12:'fi-FI',13:'sv-SE',14:'da-DK',15:'nb-NO',16:'pl-PL',17:'pt-BR',
            18:'en-GB',19:'tr-TR',20:'es-419',21:'ar',22:'fr-CA'}

def entries(raw):
    if not 96<=len(raw)<=32*1024*1024:raise ValueError('PS4 TRP size outside bounds')
    magic,version,size,count,stride=struct.unpack_from('>IIQII',raw)
    if (magic,version,size,stride)!=(0xdca24d00,3,len(raw),64) or not 1<=count<=4096 or 96+count*64>size:
        raise ValueError('Unsupported PS4 TRP header')
    if hashlib.sha1(raw[:28]+bytes(20)+raw[48:]).digest()!=raw[28:48]:raise ValueError('PS4 TRP checksum mismatch')
    files,ranges={},[]
    for i in range(count):
        at=96+i*64;name_bytes=raw[at:at+32]
        try:name=name_bytes.split(b'\0',1)[0].decode('ascii')
        except UnicodeError:raise ValueError('Invalid PS4 TRP name') from None
        if not name or name in ('.','..') or any(ord(c)<32 or ord(c)>126 or c in '/\\' for c in name) or name_bytes!=name.encode().ljust(32,b'\0') or name in files:
            raise ValueError('Unsafe/duplicate PS4 TRP entry')
        offset,length=struct.unpack_from('>QQ',raw,at+32)
        if offset<96+count*64 or offset+length>size:raise ValueError('PS4 TRP entry outside bounds')
        if length:ranges.append((offset,offset+length))
        files[name]=raw[offset:offset+length]
    ranges.sort()
    if any(a[1]>b[0] for a,b in zip(ranges,ranges[1:])):raise ValueError('Overlapping PS4 TRP entries')
    return files

def definition(raw,title):
    if not 32<=len(raw)<=1024*1024 or len(raw)%16:raise ValueError('Invalid ESFM bounds')
    key=AES.new(_FORMAT_KEY,AES.MODE_CBC,bytes(16)).encrypt(title.encode().ljust(16,b'\0'))
    text=AES.new(key,AES.MODE_CBC,raw[:16]).decrypt(raw[16:])
    padding=text[-1]
    if 1<=padding<=16 and text[-padding:]==bytes([padding])*padding:text=text[:-padding]
    text=text.rstrip(b'\0').decode('utf-8-sig')
    if '<!DOCTYPE' in text.upper() or '<!ENTITY' in text.upper():raise ValueError('XML entities forbidden')
    root=ET.fromstring(text)
    def leaf(parent,name,required=True):
        nodes=parent.findall(name)
        if len(nodes)>1 or (required and len(nodes)!=1) or any(len(n) or n.attrib for n in nodes):
            raise ValueError('Invalid/duplicate PS4 metadata field')
        return nodes[0].text if nodes else None
    if root.tag!='trophyconf' or leaf(root,'npcommid')!=title or len(list(root.iter()))>10000:
        raise ValueError('PS4 metadata identity/schema mismatch')
    label=leaf(root,'title-name')
    if not isinstance(label,str) or not 1<=len(label)<=200:raise ValueError('Invalid PS4 title name')
    texts={'':(label,'')};info={};grades={}
    for item in root.findall('trophy'):
        raw_id=item.get('id','');hidden=item.get('hidden');grade=_GRADES.get(item.get('ttype'))
        if not re.fullmatch('[0-9]{1,4}',raw_id) or hidden not in ('yes','no') or not grade:raise ValueError('Invalid PS4 trophy definition')
        identity=str(int(raw_id));name=leaf(item,'name');detail=leaf(item,'detail',False) or ''
        if identity in info or not isinstance(name,str) or not 1<=len(name)<=200 or len(detail)>4000:
            raise ValueError('Invalid/duplicate PS4 trophy text')
        info[identity]=(hidden=='yes',detail);grades[identity]=grade;texts[identity]=(name,detail)
    if not 1<=len(info)<=2000 or set(info)!={str(i) for i in range(len(info))}:raise ValueError('Incomplete PS4 trophy definitions')
    return info,texts,grades

def read_package(raw,title):
    if not re.fullmatch('NPWR[0-9]{5}_00',title):raise ValueError('Invalid PS4 set identifier')
    files=entries(raw);info,base,grades=definition(files['TROP.ESFM'],title)
    texts={};default='en-US'
    for name,encoded in files.items():
        match=re.fullmatch(r'TROP_([0-9]{2})\.ESFM',name)
        if not match or int(match[1]) not in _LANGUAGES:continue
        locale=_LANGUAGES[int(match[1])];other,localized,other_grades=definition(encoded,title)
        if other.keys()!=info.keys() or other_grades!=grades or any(other[k][0]!=info[k][0] for k in info):
            raise ValueError('PS4 localized definitions differ')
        texts[locale]=localized
    if 'en-US' in texts:
        if texts['en-US']!=base:raise ValueError('PS4 default/English metadata differ')
    else:
        # Preserve the publisher default without inventing its language.
        default='und';texts[default]=base
    images={'':png(files['ICON0.PNG'])}
    for identity in info:
        name=f'TROP{int(identity):03d}.PNG'
        if name in files:images[identity]=png(files[name])
    return {'format':'ps4_trp_v3','trp_sha1':raw[28:48].hex(),'info':info,'texts':texts,
            'default':default,'grades':grades},images
