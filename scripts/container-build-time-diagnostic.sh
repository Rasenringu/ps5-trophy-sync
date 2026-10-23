#!/usr/bin/env bash
set -euo pipefail
cd /workspace
deps=/workspace/.local/console-build
mkdir -p artifacts/console/time-diagnostic
/opt/ps5-payload-sdk/bin/prospero-clang -Wall -Wextra -Werror -Wno-unused-command-line-argument -O2 -nostartfiles \
  -DPS5_SQLITE_DESCRIPTOR_STAT -I"$deps/sqlite-amalgamation-3530400" \
  console/tests/time_diagnostic.c console/readers/schema_probe.c \
  "$deps/probe-build/sqlite3.o" console/build/crt-readonly.o \
  -lSceUserService -o artifacts/console/time-diagnostic/TimeDiagnostic.elf
python3 console/verify-elf.py artifacts/console/time-diagnostic/TimeDiagnostic.elf
