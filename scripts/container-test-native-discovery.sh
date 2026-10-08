#!/usr/bin/env bash
set -euo pipefail
cd /workspace
cc -std=c11 -Wall -Wextra -Werror -Wno-misleading-indentation -O1 -g -fsanitize=address,undefined -ffunction-sections -fdata-sections -Wl,--gc-sections -DNATIVE_DISCOVERY_TEST console/tests/native_discovery_cli.c console/sync/native_discovery_ftp.c  -o .local/console-build/probe-build/native-discovery-cli
python3 console/tests/test_native_discovery.py .local/console-build/probe-build/native-discovery-cli
