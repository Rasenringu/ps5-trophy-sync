#!/usr/bin/env bash
set -euo pipefail
cd /workspace
deps=/workspace/.local/console-build
cc -std=c11 -O1 -g -Wall -Wextra -Werror -fsanitize=address,undefined console/readers/native_join.c console/tests/test_native_join.c -o "$deps/probe-build/test-native-join"
"$deps/probe-build/test-native-join"
cc -std=c11 -O1 -g -Wall -Wextra -Werror -fsanitize=address,undefined -I"$deps/mbedtls-3.6.7/include" -I"$deps/sqlite-amalgamation-3530400" console/tests/native_join_cli.c console/readers/native_join.c console/readers/native_state.c console/readers/ucp.c console/readers/native_definitions.c "$deps/probe-build/sqlite3-host.o" "$deps/mbedtls-host-linux-build/library/libmbedcrypto.a" -o "$deps/probe-build/native-join-cli"
python3 console/tests/test_native_join_capture.py "$deps/probe-build/native-join-cli" .local/captures/native-format-prefixes
/opt/ps5-payload-sdk/bin/prospero-clang -Wall -Wextra -Werror -O2 -c console/readers/native_join.c -o "$deps/probe-build/native-join-ps5.o"
echo 'PASS PS5 compile: native ID join; no ELF sent.'
