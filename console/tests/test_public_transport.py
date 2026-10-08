"""Opt-in hosted HTTPS checks: no account/device creation, tokens or imports."""
import subprocess
from pathlib import Path
root = Path(__file__).resolve().parents[2]
build = root / '.local/console-build/probe-build'
ca = root / 'console/vendor/public-service-ca.pem'
for binary, path, extra in [('https-json-cli', '/api/device/status', []),
                            ('https-binary-cli', '/api/device/artwork', ['96'])]:
    command = [str(build / binary), '443', 'trophy-sync.party', str(ca), path,
               'trophy-sync.party', *extra]
    result = subprocess.check_output(command, text=True, timeout=25).split()
    assert result[:4] == ['0', '0', '1', '401'], result
    command[2] = 'wrong-host.invalid'
    result = subprocess.check_output(command, text=True, timeout=25).split()
    assert result[0] != '0' and result[2] == '0', result
print('PASS hosted Mbed TLS JSON/binary: DNS, TLS 1.2, roots, hostname, unauthenticated 401, wrong-host rejection. No pairing/import or console validation.')
