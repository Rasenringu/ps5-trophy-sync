#!/usr/bin/env bash
set -euo pipefail
cd /workspace
deps=/workspace/.local/console-build
cc -std=c11 -O1 -g -Wall -Wextra -Werror -fsanitize=address,undefined \
  console/tests/test_ps4_image_snapshot.c -o "$deps/probe-build/test-ps4-image-snapshot"
"$deps/probe-build/test-ps4-image-snapshot"
bash /workspace/scripts/container-build-ps4-copy-inspect.sh
