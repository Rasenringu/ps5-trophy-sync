"""Synthetic definitions + optional actual private capture validation, no console."""
import hashlib
import json
import struct
import subprocess
import sys
import tempfile
from pathlib import Path
def container(conf,metadata):
    entries={'tropconf.json':json.dumps(conf,ensure_ascii=True).encode(),'tropmeta_en-US.json':json.dumps(metadata,ensure_ascii=True).encode()}
    b=bytearray(96+64*len(entries));records=[]
    for i,(name,data) in enumerate(sorted(entries.items())):
        offset=len(b);b.extend(data);b.extend(bytes(16-len(b)%16));records.append((i,name,offset,len(data)))
    struct.pack_into('>IIQII',b,0,0xb228c60a,1,len(b),len(entries),64)
    for i,name,offset,length in records:
        base=96+i*64;encoded=name.encode();b[base:base+len(encoded)]=encoded;struct.pack_into('>QQ',b,base+32,offset,length)
    b[28:48]=hashlib.sha1(b).digest();return b
def fixture():
    conf={'schemaVersion':'0.90','trophyDefinitionRevision':1,'trophySetVersion':'01.00','trophyNpCommId':'NPWR00000_00','defaultLanguage':'en-US','platform':['PS5'],'trophies':[{'id':'custom-id','grade':'B','hidden':False}]}
    meta={k:v for k,v in conf.items() if k in ('schemaVersion','trophyDefinitionRevision','trophySetVersion','trophyNpCommId')}
    meta['metadata']={'titleMetadata':{'name':'MOCK 雪'},'trophyMetadata':[{'id':'custom-id','name':'MOCK trophy 🏆'}]}
    return conf,meta
with tempfile.TemporaryDirectory(prefix='MOCK-definitions-') as temp:
    path=Path(temp)/'fixture.ucp'
    def run(c,m):
        path.write_bytes(container(c,m));return subprocess.check_output([sys.argv[1],str(path)],text=True,timeout=5).split()
    assert run(*fixture())==['0','1','1','0','0','0']
    c,m=fixture();c['schemaVersion']='1.00'
    assert run(c,m)==['0','1','1','0','0','0'], 'Config1.00 uses localized metadata0.90 in actual captures'
    for mutation in ('grade','duplicate','mismatch','missing_name','id_type','nul','unicode_length','schema','platform'):
        c,m=fixture()
        if mutation=='grade':c['trophies'][0]['grade']='unknown'
        elif mutation=='duplicate':c['trophies'].append(c['trophies'][0]);m['metadata']['trophyMetadata'].append(m['metadata']['trophyMetadata'][0])
        elif mutation=='mismatch':m['trophyDefinitionRevision']=2
        elif mutation=='missing_name':del m['metadata']['trophyMetadata'][0]['name']
        elif mutation=='id_type':c['trophies'][0]['id']=0;m['metadata']['trophyMetadata'][0]['id']=0
        elif mutation=='nul':m['metadata']['trophyMetadata'][0]['name']='MOCK\x00private'
        elif mutation=='unicode_length':m['metadata']['trophyMetadata'][0]['name']='🏆'*201
        elif mutation=='schema':c['schemaVersion']='unknown'
        elif mutation=='platform':c['platform']=['PS4']
        assert run(c,m)[0]!='0',mutation
print('PASS LOCAL native definitions: real schema shape, UTF8, grade/identity/revision/duplicate/missing/type/NUL/length/unsupported rejection; unlock state never inferred.')
if len(sys.argv)>2:
    files=sorted(Path(sys.argv[2]).glob('definitions-*.ucp'))
    for path in files:
        result=subprocess.check_output([sys.argv[1],str(path)],text=True,timeout=10).split()
        assert result[0]=='0','Private actual native capture rejected'
    print('PASS private native definition capture assertions; no new console result.' if files else 'SKIP private native definitions: none provided.')
