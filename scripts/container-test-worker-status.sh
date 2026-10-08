#!/usr/bin/env bash
set -euo pipefail
cd /workspace
deps=/workspace/.local/console-build
cc -std=c11 -Wall -Wextra -Werror -O1 -g -fsanitize=address,undefined console/tests/test_worker_status.c console/worker/status_client.c console/ui/screen.c console/vendor/qrcodegen.c -o "$deps/probe-build/test-worker-status"
"$deps/probe-build/test-worker-status"
