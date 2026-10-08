#!/usr/bin/env bash
# Host fixtures only: no console connections or payload executions.
set -euo pipefail
cd /workspace
deps=/workspace/.local/console-build
for suite in native-readers native-state native-join native-activity native-discovery worker-state worker-queue worker-import worker-status https-json https-binary; do
  bash "scripts/container-test-$suite.sh"
done
cc -std=c11 -O1 -g -Wall -Wextra -Werror -fsanitize=address,undefined -I"$deps/sqlite-amalgamation-3530400" console/tests/schema_probe_cli.c console/readers/schema_probe.c "$deps/probe-build/sqlite3-host.o" -o "$deps/probe-build/schema-cli"
python3 console/tests/test_schema_probe.py "$deps/probe-build/schema-cli"
cc -std=c11 -O1 -g -Wall -Wextra -Werror -fsanitize=address,undefined -I"$deps/probe-config" -I"$deps/sqlite-amalgamation-3530400" -I"$deps/mbedtls-3.6.7/include" console/tests/test_pair_client.c console/pairing/state.c console/ui/screen.c "$deps/probe-build/sqlite3-host.o" "$deps/mbedtls-host-linux-build/library/libmbedcrypto.a" -o "$deps/probe-build/pair-client"
"$deps/probe-build/pair-client"
cc -std=c11 -O1 -g -Wall -Wextra -Werror -fsanitize=address,undefined console/tests/test_tiled_frame.c console/ui/tiled_frame.c -o "$deps/probe-build/tiled-frame"
"$deps/probe-build/tiled-frame"
