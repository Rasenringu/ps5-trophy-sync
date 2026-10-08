#!/usr/bin/env bash
set -euo pipefail
cd /workspace
work=/workspace/.local/console-build/final-ui-host
mkdir -p "$work" artifacts/console/final-ui/previews
font=/workspace/.local/console-build/final-ui-font
cc -std=c11 -Wall -Wextra -Werror -O1 -g -fsanitize=address,undefined -I"$font" console/ui/final_preview.c console/ui/final_screen.c console/ui/screen.c console/vendor/qrcodegen.c -o "$work/preview"
for state in pairing expired connected syncing connecting error long partial; do
  "$work/preview" "$state" "artifacts/console/final-ui/previews/$state.ppm"
done
cc -std=c11 -Wall -Wextra -Werror -O2 console/tests/test_ui.c console/ui/screen.c console/vendor/qrcodegen.c -o "$work/pairing-test"
"$work/pairing-test"
