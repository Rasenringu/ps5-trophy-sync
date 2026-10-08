"""Create local development TLS material; no global trust, DNS or console writes."""
import argparse
import ipaddress
import json
import socket
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--server-ip')
    parser.add_argument('--port', type=int, default=8443)
    args = parser.parse_args()
    config_path = ROOT/'config/local.json'
    config = json.loads(config_path.read_text(encoding='utf-8-sig'))
    if not 1024 <= args.port <= 65535:
        parser.error('Choose an unprivileged port between 1024 and 65535')
    console = str(ipaddress.IPv4Address(config['ps5_ip']))
    if args.server_ip:
        address = str(ipaddress.IPv4Address(args.server_ip))
    else:
        # UDP connect chooses a route/interface without sending a datagram.
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as route:
            route.connect((console, 2121))
            address = route.getsockname()[0]
    ip = ipaddress.IPv4Address(address)
    private = any(ip in ipaddress.IPv4Network(n) for n in ('10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16'))
    if not private or address == console:
        parser.error('Server IP must be this PC\'s private LAN address, distinct from the PS5')
    origin = f'https://{address}:{args.port}'
    if config.get('service_url') not in ('', origin):
        parser.error('Configured service URL differs; refusing to replace it')
    tls = ROOT/'.local/tls'
    tls.mkdir(parents=True, exist_ok=True)
    metadata = tls/'identity.json'
    identity = {'server_ip': address, 'origin': origin, 'port': args.port, 'purpose': 'LAN_DEVELOPMENT_ONLY'}
    if metadata.exists():
        if json.loads(metadata.read_text()) != identity:
            parser.error('Existing certificate identity differs; refusing rotation')
        for name in ('ca.crt', 'ca.key', 'server.crt', 'server.key'):
            if not (tls/name).is_file():
                parser.error('Incomplete existing certificate material; inspect it before proceeding')
    else:
        if any((tls/name).exists() for name in ('ca.key', 'server.key', 'server.crt')):
            parser.error('Untracked certificate material exists; refusing replacement')
        (tls/'server.ext').write_text(
            'basicConstraints=critical,CA:FALSE\nkeyUsage=critical,digitalSignature,keyEncipherment\n'
            f'extendedKeyUsage=serverAuth\nsubjectAltName=IP:{address}\n', encoding='ascii')
        subprocess.run(['docker', 'run', '--rm', '--mount', f'type=bind,source={ROOT},target=/workspace',
                        'ps5-trophy-build:starter', 'bash', '/workspace/scripts/container-create-lan-cert.sh', address],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        metadata.write_text(json.dumps(identity, indent=2), encoding='utf-8')
    (tls/'nginx.conf').write_text('''server {
    listen 443 ssl;
    server_name _;
    ssl_certificate /etc/nginx/tls/server.crt;
    ssl_certificate_key /etc/nginx/tls/server.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_session_tickets off;
    client_max_body_size 2m;
    access_log off;
    location = /api/device/artwork {
        client_max_body_size 64m;
        proxy_pass http://lan-api:8000/device/artwork;
        proxy_set_header Host $http_host;
        proxy_set_header X-Forwarded-Proto https;
        proxy_read_timeout 60s;
    }
    location /api/ {
        proxy_pass http://lan-api:8000/;
        proxy_set_header Host $http_host;
        proxy_set_header X-Forwarded-Proto https;
        proxy_read_timeout 15s;
    }
    location / {
        proxy_pass http://web:3000;
        proxy_set_header Host $http_host;
        proxy_set_header X-Forwarded-Proto https;
        proxy_read_timeout 15s;
    }
}
''', encoding='ascii')
    (ROOT/'.local/lan-https.env').write_text(
        f'LAN_SERVICE_IP={address}\nLAN_HTTPS_PORT={args.port}\nLAN_HTTPS_ORIGIN={origin}\n', encoding='ascii')
    config['service_url'] = origin
    config_path.write_text(json.dumps(config, indent=2), encoding='utf-8')
    print('Prepared LAN HTTPS origin:', origin)
    print('Public development trust certificate:', tls/'ca.crt')


if __name__ == '__main__':
    main()
