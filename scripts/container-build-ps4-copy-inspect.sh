#!/usr/bin/env bash
set -euo pipefail
cd /workspace
deps=/workspace/.local/console-build
mkdir -p artifacts/console/ps4-copy-inspect
/opt/ps5-payload-sdk/bin/prospero-clang -Wall -Wextra -Werror -Wno-unused-command-line-argument -Wno-misleading-indentation -O2 -nostartfiles \
  -DPS5_SQLITE_DESCRIPTOR_STAT -I"$deps/sqlite-amalgamation-3530400" \
  console/tests/ps4_copy_inspect.c console/readers/ps4_image_snapshot.c console/readers/schema_probe.c \
  "$deps/probe-build/sqlite3.o" console/build/crt-readonly.o -lSceUserService \
  -o artifacts/console/ps4-copy-inspect/PS4CopyInspect.elf
python3 console/verify-elf.py artifacts/console/ps4-copy-inspect/PS4CopyInspect.elf
