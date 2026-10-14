#!/usr/bin/env bash
set -euo pipefail
cd /workspace
deps=/workspace/.local/console-build
cc -std=c11 -O1 -g -Wall -Wextra -Werror -Wno-misleading-indentation -fsanitize=address,undefined \
  -Iconsole/tests/ps4-stubs -I"$deps/mbedtls-3.6.7/include" console/tests/test_ps4_collect.c \
  console/readers/ps4_image_snapshot.c "$deps/mbedtls-host-linux-build/library/libmbedcrypto.a" \
  -o "$deps/probe-build/ps4-collect"
"$deps/probe-build/ps4-collect"
