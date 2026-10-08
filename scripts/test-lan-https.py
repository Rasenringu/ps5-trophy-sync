"""Real local TLS chain/IP checks. Never contacts the console or imports records."""
import json
import socket
import ssl
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
identity = json.loads((ROOT/'.local/tls/identity.json').read_text())
trusted = ssl.create_default_context(cafile=str(ROOT/'.local/tls/ca.crt'))
trusted.minimum_version = ssl.TLSVersion.TLSv1_2
proxy = urllib.request.ProxyHandler({})
client = urllib.request.build_opener(proxy, urllib.request.HTTPSHandler(context=trusted))
deadline = time.monotonic()+30
while True:
    try:
        health = json.load(client.open(identity['origin']+'/api/health', timeout=3))
        assert health['status'] == 'ok' and health['console_verified'] is False
        break
    except (OSError, urllib.error.URLError):
        if time.monotonic() >= deadline:
            raise
        time.sleep(1)
assert client.open(identity['origin']+'/login', timeout=5).status == 200
with socket.create_connection((identity['server_ip'], identity['port']), timeout=5) as raw:
    try:
        with trusted.wrap_socket(raw, server_hostname='wrong-host.invalid'):
            raise AssertionError('Wrong hostname accepted')
    except ssl.SSLCertVerificationError:
        pass
untrusted = urllib.request.build_opener(proxy, urllib.request.HTTPSHandler(context=ssl.create_default_context()))
try:
    untrusted.open(identity['origin']+'/api/health', timeout=5)
    raise AssertionError('Untrusted CA accepted')
except urllib.error.URLError as error:
    assert isinstance(error.reason, ssl.SSLCertVerificationError)
print('PASS LOCAL: health/login over HTTPS; correct CA/IP accepted; wrong hostname and untrusted CA rejected.')
print('This command checks local HTTPS only; see docs/STATUS.md for separate console results. No machine trust store or firewall changes made.')
