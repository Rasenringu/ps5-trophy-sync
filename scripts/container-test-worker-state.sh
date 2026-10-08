#!/usr/bin/env bash
set -euo pipefail
cc -std=c11 -Wall -Wextra -Werror -O1 -g -fsanitize=address,undefined -DPS5_ABSOLUTE_STATE -DPS5_WORKER_STATE console/tests/test_reserved_state.c -o .local/console-build/probe-build/test-worker-state
.local/console-build/probe-build/test-worker-state
cc -std=c11 -Wall -Wextra -Werror -O1 -g -fsanitize=address,undefined -DPS5_ABSOLUTE_STATE -DPS5_ZERO_LINK_STATE console/tests/test_reserved_state.c -o .local/console-build/probe-build/test-old-ui-state
.local/console-build/probe-build/test-old-ui-state

cc -std=c11 -Wall -Wextra -Werror -O1 -g -fsanitize=address,undefined -DPS5_ABSOLUTE_STATE -DPS5_WORKER_STATE -DPS5_ZERO_LINK_STATE console/tests/test_reserved_state.c -o .local/console-build/probe-build/test-worker-zero-state
.local/console-build/probe-build/test-worker-zero-state
