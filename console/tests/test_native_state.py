"""MOCK malformed-file tests plus authorized private capture/reference assertions."""
from pathlib import Path
import hashlib,json,struct,subprocess,sys,tempfile
from datetime import datetime
cli=Path(sys.argv[1]);base=Path(sys.argv[2])
epoch=62135596800000000
stamp=epoch+1704067200000000 # MOCK 2024-01-01 UTC, no console data.
def pack(logical):
    logical=logical+bytes((-len(logical))%1024)
    header=bytearray(64);header[:4]=b'T2PD';struct.pack_into('>IQ',header,4,0x10000,1056)
    struct.pack_into('>Q',header,32,len(logical)//1024)
    return bytes(header)+b''.join(logical[o:o+1024]+hashlib.sha256(logical[o:o+1024]).digest() for o in range(0,len(logical),1024))
def fixture():
    b=bytearray(1024);b[:4]=b'T2TD';struct.pack_into('>II',b,4,0x10000,2)
    struct.pack_into('>IIIIQQ',b,48,0x500,192,1,2,112,0)
    struct.pack_into('>IIIIQQ',b,80,0x800,80,1,2,528,0)
    for i in range(2):
        struct.pack_into('>IIQ',b,112+i*208,0x500,192,0);struct.pack_into('>I',b,128+i*208,i)
        struct.pack_into('>IIQ',b,528+i*96,0x800,80,0);struct.pack_into('>I',b,544+i*96,i)
    struct.pack_into('>I',b,644,17);struct.pack_into('>Q',b,656,stamp);struct.pack_into('>Q',b,672,stamp+1000000)
    return b
def run(path):
    result=subprocess.run([str(cli),str(path),'--details'],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    return json.loads(result.stdout)
with tempfile.TemporaryDirectory(prefix='MOCK-native-state-') as directory:
    path=Path(directory)/'MOCK-state.dat'
    def check(data,code):
        path.write_bytes(data);result=run(path);assert result['rc']==code,result;return result
    original=fixture();result=check(pack(original),0)
    assert (result['earned'],result['locked'],result['unknown'])==(1,1,0)
    assert result['records'][1]['first_us']==1704067200000000
    for size in [0,3,63,64,100,1119]:check(pack(original)[:size],2)
    b=bytearray(pack(original));b[64+100]^=1;check(b,3) # digest mutation
    b=bytearray(pack(original));b[-1]^=1;check(b,3)
    b=bytearray(pack(original));b[4]^=1;check(b,1)
    b=bytearray(pack(original));struct.pack_into('>Q',b,32,2**64-1);check(b,2)
    for mutate,code in [
        (lambda b:struct.pack_into('>I',b,8,2**32-1),2),
        (lambda b:struct.pack_into('>Q',b,96,2**64-1),2),
        (lambda b:struct.pack_into('>I',b,92,2**32-1),4),
        (lambda b:struct.pack_into('>I',b,84,81),4),
        (lambda b:struct.pack_into('>I',b,640,0),4), # duplicate ID
        (lambda b:struct.pack_into('>I',b,88,2),4), # unsupported schema
        (lambda b:struct.pack_into('>I',b,624,0x900),4),
        (lambda b:b.__setitem__(900,1),4), # padding corruption, valid digest
    ]:
        b=fixture();mutate(b);check(pack(b),code)
    b=fixture();struct.pack_into('>I',b,644,1)
    result=check(pack(b),0);assert result['unknown']==1 and result['records'][1]['flags']==1
    b=fixture();struct.pack_into('>Q',b,656,0)
    result=check(pack(b),0);assert result['unknown']==1 and result['records'][1]['time_known']==2
    # Actual V13 aggregate shape: flag16, absent first timestamp, valid second.
    # Preserve uncertainty instead of promoting this record to earned or locked.
    struct.pack_into('>I',b,644,16)
    result=check(pack(b),0)
    assert result['unknown']==1 and result['records'][1]['status']==0
    assert result['records'][1]['flags']==16 and result['records'][1]['time_known']==2
    b=fixture();struct.pack_into('>Q',b,656,2**64-1)
    result=check(pack(b),0);assert result['unknown']==1
capture=base/'naruto-state-investigation.dat'
if capture.exists():
    result=run(capture);assert result['rc']==0,result
    assert (result['count'],result['earned'],result['locked'],result['unknown'])==(45,6,39,0)
    earned={r['id'] for r in result['records'] if r['status']==2}
    # IDs corroborated by the six user-provided French trophy names in private
    # localized metadata investigation, not derived from this state decoder.
    assert earned=={21,25,26,27,29,31}
    training=next(r for r in result['records'] if r['id']==21)
    reference_file=base/'native-time-reference-match.json'
    if reference_file.exists():
        reference=json.loads(reference_file.read_text(encoding='utf-8'))
        minute=int(datetime.fromisoformat(reference['reference_utc']).timestamp())*1000000
        assert minute<=training['first_us']<minute+60000000
        assert minute<=training['second_us']<minute+60000000
print('PASS native state: MOCK malformed/bounds/digest/unsupported/unknown tests; private capture/reference checked when present. No console execution or imports.')
