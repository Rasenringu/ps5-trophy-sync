#!/usr/bin/env bash
set -euo pipefail
cd /workspace
deps=/workspace/.local/console-build
cc -std=c11 -Wall -Wextra -Werror -O1 -g -fsanitize=address,undefined -DPS5_ABSOLUTE_STATE -DPS5_WORKER_STATE -DPS5_ZERO_LINK_STATE -I"$deps/mbedtls-3.6.7/include" console/tests/test_worker_queue.c console/sync/queue.c "$deps/mbedtls-host-linux-build/library/libmbedcrypto.a" -o "$deps/probe-build/test-worker-queue"
"$deps/probe-build/test-worker-queue"
/opt/ps5-payload-sdk/bin/prospero-clang -Wall -Wextra -Werror -O2 -I"$deps/probe-ps5/include" -c console/sync/queue.c -o "$deps/probe-build/worker-queue-ps5.o"
