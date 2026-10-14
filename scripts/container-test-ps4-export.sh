#!/usr/bin/env bash
set -euo pipefail
cd /workspace
deps=/workspace/.local/console-build
cc -std=c11 -O1 -g -Wall -Wextra -Werror -Wno-misleading-indentation -fsanitize=address,undefined \
  -I"$deps/sqlite-amalgamation-3530400" console/sync/ps4_export.c console/tests/test_ps4_export.c \
  "$deps/probe-build/sqlite3-host.o" -lpthread -o "$deps/probe-build/ps4-export"
"$deps/probe-build/ps4-export"
cc -std=c11 -O1 -g -Wall -Wextra -Werror -Wno-misleading-indentation -fsanitize=address,undefined \
  -DPS4_EXPORT_CLI -I"$deps/sqlite-amalgamation-3530400" console/tests/ps4_state_cli.c \
  console/readers/ps4_state.c console/sync/ps4_export.c "$deps/probe-build/sqlite3-host.o" \
  -lpthread -o "$deps/probe-build/ps4-export-cli"
python3 console/tests/check_ps4_private_export.py "$deps/probe-build/ps4-export-cli"
