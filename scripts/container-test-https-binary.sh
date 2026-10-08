#!/usr/bin/env bash
set -euo pipefail
cd /workspace
deps=/workspace/.local/console-build
cc -std=c11 -Wall -Wextra -Werror -Wno-misleading-indentation -O1 -g -I"$deps/mbedtls-3.6.7/include" console/tests/https_binary_cli.c console/transport/https_binary.c "$deps/mbedtls-host-linux-build/library/libmbedtls.a" "$deps/mbedtls-host-linux-build/library/libmbedx509.a" "$deps/mbedtls-host-linux-build/library/libmbedcrypto.a" -o "$deps/probe-build/https-binary-cli"
python3 console/tests/test_https_binary.py "$deps/probe-build/https-binary-cli"
