"""Synthetic corruption/profile/unknown-state regressions and optional private captures."""
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

cli=Path(sys.argv[1])
types=[1,2,0x100,0x200,0x300,0x400,0x500,0x600,0x700,0x800]
sizes=[48,96,64,48,320,80,96,160,96,80]
counts=[1,1,1,16,1,1,2,1,1,2]
profile=0x12345678
title='NPWR00001_00'
def fixture():
    image=bytearray(368)
    struct.pack_into('>III',image,0,0x8d1f8d08,0x10000,10)
    for i,(typ,size,count) in enumerate(zip(types,sizes,counts)):
        off=len(image)
        struct.pack_into('>IIIIQQ',image,48+i*32,typ,size,1,count,off,0)
        for j in range(count):
            image+=struct.pack('>IIII',typ,size,0,0)+bytes(size)
            at=off+j*(size+16)+16
            if typ==2:struct.pack_into('>I',image,at+40,profile)
            if typ==0x200 and j==0:image[at:at+12]=b'CUSA00001_00'
            if typ==0x300:
                image[at:at+12]=title.encode();image[at+32:at+44]=title.encode()
            if typ==0x500:struct.pack_into('>II',image,at,j,4)
            if typ==0x800:
                struct.pack_into('>I',image,at,j)
                if j==1:struct.pack_into('>IIIQQ',image,at+4,1,0x2000,0,63800000000000000,63800000001000000)
    return image
def run(image,success,needle='',user=profile,set_id=title):
    with tempfile.NamedTemporaryFile() as f:
        f.write(image);f.flush()
        result=subprocess.run([str(cli),f.name,f'{user:x}',set_id],capture_output=True,text=True)
    assert (result.returncode==0)==success,(result.returncode,result.stdout,result.stderr)
    if needle:assert needle in result.stdout,result.stdout
sample=fixture();run(sample,True,'earned=1 locked=1 unknown=0')
run(sample,False,user=profile+1);run(sample,False,set_id='NPWR00002_00')
run(sample[:100],False);run(sample+bytes(1),False)
for offset,value in [(0,0x54525032),(4,0),(8,9),(48+32*9,0x500),(48+32*9+12,1)]:
    changed=sample.copy();struct.pack_into('>I',changed,offset,value);run(changed,False)
changed=sample.copy();struct.pack_into('>Q',changed,48+32*9+16,368);run(changed,False)
off=struct.unpack_from('>Q',sample,48+9*32+16)[0]
changed=sample.copy();struct.pack_into('>I',changed,off+96+16+4,0x80000001);run(changed,True,'unknown=1')
changed=sample.copy();struct.pack_into('>I',changed,off+96+16,0);run(changed,False)
changed=sample.copy();struct.pack_into('>Q',changed,off+16+16,1);run(changed,True,'unknown=1')
print('PASS MOCK PS4 state bounds, type isolation, embedded profile/title, unknown flags and timestamps')

captures=Path('captures/library-investigation/ps4-copy-inspect-v3')
expected={'NPWR09798_00':(54,0),'NPWR10954_00':(43,0),'NPWR29343_00':(45,2)}
for name,(count,earned) in expected.items():
    path=captures/(name+'-TRPTITLE.DAT')
    if not path.exists():continue
    real=path.read_bytes();useroff=struct.unpack_from('>Q',real,48+32+16)[0]
    embedded=struct.unpack_from('>I',real,useroff+16+40)[0]
    run(real,True,f'count={count} earned={earned}',user=embedded,set_id=name)
    print('PASS private PS4 source',name,'count',count,'earned',earned)
