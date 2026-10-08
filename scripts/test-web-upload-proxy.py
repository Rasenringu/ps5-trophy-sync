"""Check built Next.js rewrites with large MOCK uploads on an isolated Docker network."""
import argparse
import hashlib
import json
import subprocess
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--web-image',default='deployment-web:latest')
parser.add_argument('--size-mib',type=int,action='append')
args=parser.parse_args()
sizes=args.size_mib or [11]
if any(n<1 or n>64 for n in sizes):parser.error('Sizes must be between 1 and 64 MiB')
root=Path(__file__).resolve().parents[1]
prefix='trophysync-upload-'+uuid.uuid4().hex[:10]
sink,web=prefix+'-sink',prefix+'-web'
def docker(*command):
    return subprocess.check_output(['docker',*command],text=True).strip()
network=False
try:
    docker('network','create',prefix);network=True
    docker('run','-d','--name',sink,'--network',prefix,'--network-alias','api',
           '--mount',f'type=bind,source={root / "web/tests/upload_sink.py"},target=/sink.py,readonly',
           'deployment-api:latest','python','/sink.py')
    docker('run','-d','--name',web,'--network',prefix,'-p','127.0.0.1::3000',args.web_image)
    port=json.loads(docker('inspect',web))[0]['NetworkSettings']['Ports']['3000/tcp'][0]['HostPort']
    origin='http://127.0.0.1:'+port
    for attempt in range(40):
        try:
            with urllib.request.urlopen(origin+'/api/health',timeout=2) as r:
                assert json.load(r)['status']=='MOCK-ready'
            break
        except (OSError,AssertionError):time.sleep(.25)
    else:raise RuntimeError('Isolated Next/sink did not become ready')
    for size in sizes:
        payload=b'M'*(size*1024*1024)
        request=urllib.request.Request(origin+'/api/device/artwork',data=payload,
                                        headers={'Content-Type':'application/octet-stream'})
        try:
            with urllib.request.urlopen(request,timeout=45) as r:
                status=r.status;result=json.load(r)
        except urllib.error.HTTPError as e:
            status=e.code;result=json.loads(e.read())
        assert status==200 and result['mock'] and result['received']==len(payload) and result['sha256']==hashlib.sha256(payload).hexdigest(),(status,result)
        print(f'PASS MOCK Next rewrite: complete {size} MiB body/hash received; no database/token/console involved.')
except Exception:
    if network:
        for name in (sink,web):
            subprocess.run(['docker','logs',name],check=False)
    raise
finally:
    if network:
        for name in (web,sink):subprocess.run(['docker','rm','-f',name],capture_output=True)
        subprocess.run(['docker','network','rm',prefix],capture_output=True)
