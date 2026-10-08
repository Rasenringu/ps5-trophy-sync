#!/usr/bin/env bash
set -euo pipefail
make -C "$PS5_PAYLOAD_SDK/samples/hello_world" clean all
printf '%s\n' 'SDK smoke compile passed locally. No console contacted.'
