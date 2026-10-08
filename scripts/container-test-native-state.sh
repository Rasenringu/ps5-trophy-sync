#!/usr/bin/env bash
set -euo pipefail
cd /workspace
deps=/workspace/.local/console-build
cc -std=c11 -O1 -g -Wall -Wextra -Werror -fsanitize=address,undefined \
  -I"$deps/mbedtls-3.6.7/include" console/readers/native_state.c console/tests/native_state_cli.c \
  "$deps/mbedtls-host-linux-build/library/libmbedcrypto.a" -o "$deps/probe-build/native-state-cli"
python3 console/tests/test_native_state.py "$deps/probe-build/native-state-cli" .local/captures/native-format-prefixes
/opt/ps5-payload-sdk/bin/prospero-clang -Wall -Wextra -Werror -O2 \
  -I"$deps/probe-ps5/include" -c console/readers/native_state.c -o "$deps/probe-build/native-state-ps5.o"
echo 'PASS native state decoder PS5 compile; no ELF sent, no live snapshot validation.'
