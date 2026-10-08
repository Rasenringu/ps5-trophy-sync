#!/usr/bin/env bash
set -euo pipefail
cd /workspace
deps=/workspace/.local/console-build
cc -std=c11 -Wall -Wextra -Werror -O1 -g -I"$deps/mbedtls-3.6.7/include" \
  console/tests/https_json_cli.c console/transport/https_json.c \
  "$deps/mbedtls-host-linux-build/library/libmbedtls.a" \
  "$deps/mbedtls-host-linux-build/library/libmbedx509.a" \
  "$deps/mbedtls-host-linux-build/library/libmbedcrypto.a" -o "$deps/probe-build/https-json-cli"
python3 console/tests/test_https_json.py "$deps/probe-build/https-json-cli"
cc -std=c11 -Wall -Wextra -Werror -Wno-unused-function -O1 -g -fsanitize=address,undefined -I"$deps/mbedtls-3.6.7/include" console/tests/test_dns_deadline.c -lpthread -o "$deps/probe-build/test-dns-deadline"
"$deps/probe-build/test-dns-deadline"
