#!/usr/bin/env bash
set -euo pipefail
cd /workspace
deps=/workspace/.local/console-build
cc -std=c11 -O1 -g -Wall -Wextra -Werror -fsanitize=address,undefined -ffunction-sections -fdata-sections -Wl,--gc-sections -DPS5_ABSOLUTE_STATE -DPS5_WORKER_STATE -DPS5_ZERO_LINK_STATE -I"$deps/probe-config" -I"$deps/mbedtls-3.6.7/include" -I"$deps/sqlite-amalgamation-3530400" console/tests/test_worker_import.c console/sync/queue.c console/sync/native_export.c console/readers/native_join.c console/worker/status.c console/ui/screen.c console/vendor/qrcodegen.c "$deps/probe-build/sqlite3-host.o" "$deps/mbedtls-host-linux-build/library/libmbedcrypto.a" -lpthread -o "$deps/probe-build/test-worker-import"
"$deps/probe-build/test-worker-import"
