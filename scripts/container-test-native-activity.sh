#!/usr/bin/env bash
set -euo pipefail
cd /workspace
deps=/workspace/.local/console-build
cc -Wall -Wextra -Werror -Wno-misleading-indentation -O1 -g -fsanitize=address,undefined \
 -DNATIVE_ACTIVITY_TEST -DPS5_SQLITE_DESCRIPTOR_STAT -I"$deps/sqlite-amalgamation-3530400" -I"$deps/mbedtls-3.6.7/include" \
 console/tests/native_activity_cli.c console/readers/native_activity.c console/readers/schema_probe.c \
 "$deps/probe-build/sqlite3-host.o" "$deps/mbedtls-host-linux-build/library/libmbedcrypto.a" -o "$deps/probe-build/native-activity-cli"
python3 console/tests/test_native_activity.py "$deps/probe-build/native-activity-cli"
/opt/ps5-payload-sdk/bin/prospero-clang -Wall -Wextra -Werror -Wno-unused-command-line-argument -O2 \
 -I"$deps/sqlite-amalgamation-3530400" -I"$deps/probe-ps5/include" -c console/readers/native_activity.c -o "$deps/probe-build/native-activity.o"
