"""Synthetic artwork fixtures; no console reads or hardware claims."""
import hashlib
import json
import struct
import zlib
import pytest
from app.console_artwork import png, entries, read_artwork, read_trophy_info

def image(width=1):
    def chunk(kind,body):
        return struct.pack('>I',len(body))+kind+body+struct.pack('>I',zlib.crc32(kind+body)&0xffffffff)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,1,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(b'\0\xff\0\0\xff'))+chunk(b'IEND',b'')

def package(files):
    b=bytearray(96+64*len(files))
    for i,(name,content) in enumerate(files.items()):
        row=96+i*64;b[row:row+32]=name.encode().ljust(32,b'\0')
        struct.pack_into('>QQ',b,row+32,len(b),len(content));b.extend(content)
    struct.pack_into('>IIQII',b,0,0xb228c60a,1,len(b),len(files),64)
    b[28:48]=hashlib.sha1(b).digest()
    return bytes(b)

def test_png_rejects_truncation_crc_dimensions_and_trailing_data():
    good=image();assert png(good)==good
    for bad in (good[:-1],good+b'extra',image(2049),good[:40]+bytes([good[40]^1])+good[41:],b'<svg/>'):
        with pytest.raises(ValueError):png(bad)

def test_ucp_icons_map_numeric_ids_and_validate_container():
    conf={'schemaVersion':'1.00','platform':['PS5'],'trophyNpCommId':'NPWR12345_00','defaultLanguage':'en-US','trophies':[{'id':'0021'}]}
    data=package({'tropconf.json':json.dumps(conf).encode(),'trop0021.png':image(),'icon0_en-US.png':image()})
    title,assets=read_artwork(data);assert title=='NPWR12345_00' and set(assets)=={'','0021'}
    bad=bytearray(data);bad[-1]^=1
    with pytest.raises(ValueError):entries(bytes(bad))
    with pytest.raises(ValueError):entries(package({'../icon.png':image()}))
    with pytest.raises(ValueError):read_artwork(package({'tropconf.json':b'{"schemaVersion":"1.00","schemaVersion":"0.90"}'}))

def test_hidden_flag_description_join_and_revision_are_exact():
    conf={'trophyNpCommId':'NPWR12345_00','trophyDefinitionRevision':'1','trophySetVersion':'1','defaultLanguage':'en-US','trophies':[{'id':'0021','hidden':True}]}
    meta={**{k:conf[k] for k in ('trophyNpCommId','trophyDefinitionRevision','trophySetVersion')},'schemaVersion':'0.90','metadata':{'trophyMetadata':[{'id':'0021','detail':'MOCK secret description'}]}}
    def encoded():return package({'tropconf.json':json.dumps(conf).encode(),'tropmeta_en-US.json':json.dumps(meta).encode()})
    assert read_trophy_info(encoded())==('NPWR12345_00',{'0021':(True,'MOCK secret description')})
    conf['trophies'][0]['hidden']='true'
    with pytest.raises(ValueError):read_trophy_info(encoded())
    conf['trophies'][0]['hidden']=True;meta['trophyDefinitionRevision']='2'
    with pytest.raises(ValueError):read_trophy_info(encoded())
