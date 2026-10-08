#!/usr/bin/env bash
set -euo pipefail
cd /workspace
deps=/workspace/.local/console-build
cc -std=c11 -O1 -g -Wall -Wextra -Werror -fsanitize=address,undefined \
  -I"$deps/mbedtls-3.6.7/include" console/readers/ucp.c console/tests/ucp_cli.c \
  "$deps/mbedtls-host-linux-build/library/libmbedcrypto.a" -o "$deps/probe-build/ucp-cli"
python3 console/tests/test_ucp.py "$deps/probe-build/ucp-cli" .local/captures/native-format-prefixes
/opt/ps5-payload-sdk/bin/prospero-clang -Wall -Wextra -Werror -O2 \
  -I"$deps/probe-ps5/include" -c console/readers/ucp.c -o "$deps/probe-build/ucp-ps5.o"
echo 'PASS native UCP reader PS5 compile; no ELF sent.'
cc -std=c11 -O1 -g -Wall -Wextra -Werror -fsanitize=address,undefined \
  -I"$deps/mbedtls-3.6.7/include" -I"$deps/sqlite-amalgamation-3530400" \
  console/readers/ucp.c console/readers/native_definitions.c console/tests/native_definitions_cli.c \
  "$deps/mbedtls-host-linux-build/library/libmbedcrypto.a" "$deps/probe-build/sqlite3-host.o" \
  -o "$deps/probe-build/native-definitions-cli"
python3 console/tests/test_native_definitions.py "$deps/probe-build/native-definitions-cli" .local/captures/native-format-prefixes
/opt/ps5-payload-sdk/bin/prospero-clang -Wall -Wextra -Werror -O2 \
  -I"$deps/probe-ps5/include" -I"$deps/sqlite-amalgamation-3530400" \
  -c console/readers/native_definitions.c -o "$deps/probe-build/native-definitions-ps5.o"
echo 'PASS native definition decoder PS5 compile; no ELF sent.'
