#!/usr/bin/env bash
set -euo pipefail
cd /workspace
mkdir -p artifacts/console/final-ui
sdk=/opt/ps5-payload-sdk
deps=/workspace/.local/console-build
flags=(-Wall -Wextra -Werror -Wno-unused-command-line-argument -O2 -nostartfiles
 -DPS5_NATIVE_STATE -DPS5_RESERVED_STATE -DPS5_ABSOLUTE_STATE -DPS5_WORKER_STATE
 -DPS5_SQLITE_DESCRIPTOR_STAT -DPS5_ZERO_LINK_STATE -DPS5_DIAGNOSTIC_SOCKET '-DPAIR_STATE_DIRECTORY="/data/trophy-sync-worker"'
 -I"$deps/probe-config" -I"$deps/probe-ps5/include" -I"$deps/sqlite-amalgamation-3530400")
"$sdk/bin/prospero-clang" "${flags[@]}" console/worker/main.c console/worker/status.c console/pairing/client.c console/pairing/state.c console/sync/queue.c console/sync/native_export.c console/sync/native_collect_assets.c console/sync/native_discovery_ftp.c console/readers/native_activity.c console/readers/schema_probe.c console/readers/ucp.c console/readers/native_definitions.c console/readers/native_state.c console/readers/native_join.c console/transport/https_json.c console/transport/https_binary.c console/ui/screen.c console/vendor/qrcodegen.c "$deps/probe-build/sqlite3.o" "$deps/probe-ps5/lib/libmbedtls.a" "$deps/probe-ps5/lib/libmbedx509.a" "$deps/probe-ps5/lib/libmbedcrypto.a" console/build/crt-readonly.o -lpthread -lSceUserService -o artifacts/console/final-ui/TrophySync.elf
python3 console/verify-elf.py artifacts/console/final-ui/TrophySync.elf
