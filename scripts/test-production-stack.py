"""Probe an isolated local production stack; never starts/publishes a tunnel.

Creates a synthetic account and pairing in that test stack. Browser TLS/domain
validation is a separate deployment check; this probes the private HTTP hop.
"""
import argparse
import json
import uuid
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from urllib.parse import urlsplit

parser=argparse.ArgumentParser()
parser.add_argument('--url',default='http://localhost:3001')
parser.add_argument('--origin',default='https://trophysync.example')
args=parser.parse_args()
assert urlsplit(args.url).hostname in ('localhost','127.0.0.1'), 'Use an isolated local test stack'
base=args.url.rstrip('/');origin=args.origin

def call(path,body=None,headers=None,binary=False):
    h=dict(headers or {})
    if body is not None:
        h['origin']=origin
        h['content-type']='application/octet-stream' if binary else 'application/json'
        if not binary:body=json.dumps(body).encode()
    try:r=urlopen(Request(base+path,data=body,headers=h),timeout=60)
    except HTTPError as error:r=error
    content=r.read()
    return r.code,r.headers,json.loads(content) if content.startswith((b'{',b'[')) else content

assert call('/api/health')[0]==200
status,headers,_=call('/api/auth/register',{'email':'production-fixture-'+uuid.uuid4().hex+'@example.test','password':'production-test-password-123'})
assert status==201
cookie=headers['set-cookie']
assert 'Secure' in cookie and 'HttpOnly' in cookie and 'SameSite=strict' in cookie
session=cookie.split(';')[0]
auth={'cookie':session}
assert call('/api/account/profile',headers=auth)[0]==200
req=Request(base+'/api/account/profile',data=b'{}',headers={'origin':'https://wrong.example','content-type':'application/json',**auth})
try:urlopen(req);raise AssertionError('Wrong origin accepted')
except HTTPError as error:assert error.code==403
status,headers,_=call('/login')
assert status==200 and headers['x-frame-options']=='DENY'
assert headers['strict-transport-security']=='max-age=31536000' and 'x-powered-by' not in headers
assert call('/test')[0]==404
_,_,installation=call('/api/device/installations',{})
status,_,pairing=call('/api/device/pairings',{'installation_id':installation['installation_id'],'profile_id':'PRODUCTION_FIXTURE','profile_label':'Production fixture'},headers={'authorization':'Bearer '+installation['installation_secret']})
assert status==201
_,_,inspection=call('/api/account/pairings/inspect',{'code':pairing['user_code']},auth)
assert call('/api/account/pairings/approve',{'code':pairing['user_code'],'pairing_id':inspection['pairing_id'],'physical_possession':True},auth)[0]==200
_,_,credential=call('/api/device/pairings/poll',{'device_code':pairing['device_code']})
device={'authorization':'Bearer '+credential['device_token']}
# Larger than common frontend proxy limits, deliberately invalid package.
# Reaching the API parser (422) proves the bounded upload bypasses the web proxy.
assert call('/api/device/artwork',b'\0'*(16*1024*1024),device,binary=True)[0]==422
assert call('/api/device/sync',{'schema_version':1,'batch_id':str(uuid.uuid4()),'source':'ps5_native','mock':True,'trophies':[],'activities':[]},device)[0]==422
print('PASS isolated production gateway: routing, secure cookie flags, authentication, origin rejection, security headers, disabled demos and authenticated 16MiB upload reaching API validation. No tunnel or public TLS validation claimed.')
