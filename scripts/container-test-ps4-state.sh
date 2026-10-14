#!/usr/bin/env bash
set -euo pipefail
cd /workspace
deps=/workspace/.local/console-build
cc -std=c11 -O1 -g -Wall -Wextra -Werror -Wno-misleading-indentation -fsanitize=address,undefined \
  console/readers/ps4_state.c console/tests/ps4_state_cli.c -o "$deps/probe-build/ps4-state-cli"
python3 console/tests/test_ps4_state.py "$deps/probe-build/ps4-state-cli"
/opt/ps5-payload-sdk/bin/prospero-clang -Wall -Wextra -Werror -Wno-misleading-indentation -O2 \
  -c console/readers/ps4_state.c -o "$deps/probe-build/ps4-state-ps5.o"
