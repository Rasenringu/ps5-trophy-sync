#!/usr/bin/env bash
set -euo pipefail
cd /workspace
mkdir -p artifacts/console/ps4-capability
/opt/ps5-payload-sdk/bin/prospero-clang -Wall -Wextra -Werror -Wno-unused-command-line-argument -O2 -nostartfiles \
  console/tests/ps4_capability_probe.c console/build/crt-readonly.o \
  -o artifacts/console/ps4-capability/PS4Capability.elf
python3 console/verify-elf.py artifacts/console/ps4-capability/PS4Capability.elf
