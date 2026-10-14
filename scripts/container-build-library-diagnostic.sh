#!/usr/bin/env bash
set -euo pipefail
cd /workspace
deps=/workspace/.local/console-build
mkdir -p artifacts/console/library-diagnostic
/opt/ps5-payload-sdk/bin/prospero-clang -Wall -Wextra -Werror -Wno-unused-command-line-argument -O2 -nostartfiles \
  -DPS5_SQLITE_DESCRIPTOR_STAT -I"$deps/probe-ps5/include" -I"$deps/sqlite-amalgamation-3530400" \
  console/tests/library_diagnostic.c console/readers/native_activity.c console/readers/schema_probe.c \
  "$deps/probe-build/sqlite3.o" "$deps/probe-ps5/lib/libmbedcrypto.a" console/build/crt-readonly.o \
  -lSceUserService -o artifacts/console/library-diagnostic/LibraryDiagnostic.elf
python3 console/verify-elf.py artifacts/console/library-diagnostic/LibraryDiagnostic.elf
