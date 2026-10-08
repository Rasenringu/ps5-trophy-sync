"""Anonymous route reachability audit; account/device creation tested locally only."""
import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--origin', default='https://trophy-sync.party')
parser.add_argument('--report', default='artifacts/tests/public-api-routes.json')
args = parser.parse_args()
origin = args.origin.rstrip('/')
if not re.fullmatch(r'https://[a-zA-Z0-9.-]+(?::[0-9]+)?|http://(?:localhost|127\.0\.0\.1)(?::[0-9]+)?', origin):
    parser.error('Use an HTTPS origin or local loopback HTTP origin')
curl = shutil.which('curl.exe') or shutil.which('curl')
if not curl:
    parser.error('curl is required')

def request(method, path):
    command = [curl, '--silent', '--show-error', '--max-time', '20', '--request', method,
               '--header', 'Origin: ' + origin, '--write-out', '\n%{http_code}', origin + '/api' + path]
    if method == 'POST':
        command += ['--header', 'Content-Type: application/json', '--data', '{}']
    output = subprocess.check_output(command, text=True, timeout=25)
    body, status = output.rsplit('\n', 1)
    return int(status), body

status, body = request('GET', '/openapi.json')
if status != 200:
    raise SystemExit(f'OpenAPI route returned {status}; check tunnel/WAF/proxy configuration')
schema = json.loads(body)
results = []
for path, methods in schema['paths'].items():
    for method in methods:
        method = method.upper()
        if method not in ('GET', 'POST'):
            continue
        if path in ('/device/installations', '/auth/logout'):
            results.append({'method': method, 'path': path, 'result': 'SKIP',
                            'reason': 'Successful write path covered by isolated API tests'})
            print('SKIP', method, path)
            continue
        probe = re.sub(r'\{[^}]+\}', '00000000-0000-4000-8000-000000000000', path)
        if path.startswith('/account/'):
            expected = 401
        elif path.startswith('/players/'):
            expected = 404
        elif path == '/health':
            expected = 200
        elif path in ('/players', '/auth/register', '/auth/login', '/device/pairings', '/device/pairings/poll'):
            expected = 422
        elif path.startswith('/device/'):
            expected = 401
        else:
            raise SystemExit('Review safety/expected response for new route: ' + path)
        status, _ = request(method, probe)
        passed = status == expected
        results.append({'method': method, 'path': path, 'status': status,
                        'expected': expected, 'result': 'PASS' if passed else 'FAIL'})
        print('PASS' if passed else 'FAIL', method, path, status, 'expected', expected)
report = Path(args.report)
report.parent.mkdir(parents=True, exist_ok=True)
report.write_text(json.dumps({'origin': origin, 'scope': 'anonymous reachability/auth/validation only',
                              'routes': results}, indent=2) + '\n', encoding='utf-8')
print('No accounts/installations created, credentials supplied or imports performed.')
raise SystemExit(1 if any(r['result'] == 'FAIL' for r in results) else 0)
