"""Generated LOCAL malformed-container tests; actual captures optional and ignored."""
import hashlib
import struct
import subprocess
import sys
import tempfile
from pathlib import Path
def digest(b):
    b[28:48]=bytes(20);b[28:48]=hashlib.sha1(b).digest();return b
def fixture():
    b=bytearray(256);struct.pack_into('>IIQII',b,0,0xb228c60a,1,len(b),2,64)
    for i,name in enumerate((b'a.json',b'tropconf.json')):
        base=96+i*64;b[base:base+len(name)]=name
        struct.pack_into('>QQ',b,base+32,224+i*16,2);b[224+i*16:226+i*16]=b'{}'
    return digest(b)
with tempfile.TemporaryDirectory(prefix='MOCK-ucp-') as temp:
    p=Path(temp)/'fixture.ucp'
    def run(b):
        p.write_bytes(b)
        return subprocess.check_output([sys.argv[1],str(p)],text=True,timeout=5).split()
    assert run(fixture())==['0','2','1']
    for size in (0,4,95,96,159,224):assert run(fixture()[:size])[0]!='0'
    bad=fixture();bad[0]^=1;assert run(digest(bad))[0]=='1'
    bad=fixture();bad[240]^=1;assert run(bad)[0]=='3'
    bad=fixture();struct.pack_into('>Q',bad,128,(1<<64)-1);assert run(digest(bad))[0]=='2'
    bad=fixture();struct.pack_into('>Q',bad,136,(1<<64)-1);assert run(digest(bad))[0]=='2'
    bad=fixture();struct.pack_into('>Q',bad,192,224);assert run(digest(bad))[0]=='2'
    bad=fixture();bad[160:192]=bad[96:128];assert run(digest(bad))[0]=='4'
    bad=fixture();bad[96:128]=b'../a'+bytes(28);assert run(digest(bad))[0]=='4'
    bad=fixture();struct.pack_into('>I',bad,16,4097);assert run(digest(bad))[0]=='2'
print('PASS LOCAL UCP: truncation, version/magic, digest mismatch, overflow, overlap, duplicate/path names and count bounds.')
if len(sys.argv)>2:
    files = sorted(Path(sys.argv[2]).glob('definitions-*.ucp'))
    for p in files:
        output=subprocess.check_output([sys.argv[1],str(p)],text=True,timeout=10).split()
        assert output[0]=='0' and output[2]=='1', 'Actual private capture rejected'
    print('PASS private UCP capture assertions; no new console result.' if files else 'SKIP private UCP captures: none provided.')
