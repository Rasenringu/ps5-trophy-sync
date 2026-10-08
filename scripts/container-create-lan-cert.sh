#!/usr/bin/env bash
set -euo pipefail
cd /workspace/.local/tls
[[ ! -e ca.key && ! -e server.key && ! -e server.crt ]] || { echo 'Existing certificate material; refusing replacement.'; exit 1; }
umask 077
openssl req -x509 -newkey rsa:3072 -nodes -sha256 -days 90 \
  -keyout ca.key -out ca.crt -subj '/CN=PS5 Trophy Sync LAN Development CA' \
  -addext 'basicConstraints=critical,CA:TRUE,pathlen:0' \
  -addext 'keyUsage=critical,keyCertSign,cRLSign'
openssl req -new -newkey rsa:3072 -nodes -sha256 \
  -keyout server.key -out server.csr -subj '/CN=PS5 Trophy Sync LAN Development'
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
  -out server.crt -sha256 -days 30 -extfile server.ext
openssl verify -CAfile ca.crt -verify_ip "$1" server.crt
