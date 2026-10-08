#!/usr/bin/env bash
set -euo pipefail
cd /workspace
bash scripts/container-prepare-title.sh
sdk=/opt/ps5-payload-sdk
deps=/workspace/.local/console-build
tool="$deps/title-build/native-tool"
native="$deps/ps5-native-app-boilerplate-2f672d1c2f508e26f82ce6e27cef289a0861413c/tooling/native"
work="$deps/final-ui-native"
mkdir -p "$work"
flags=(-target x86_64-sie-ps5 -fvisibility-nodllstorageclass=default -isysroot "$sdk"
  -isystem "$sdk/target/include/c++/v1" -isystem "$sdk/target/include"
  -DPS5_DIAGNOSTIC_SOCKET
  -fstack-usage -fno-stack-protector -fno-plt -femulated-tls -O2 -Wall -Wextra -Werror
  -I"$deps/probe-config" -I"$deps/probe-ps5/include" -I"$deps/sqlite-amalgamation-3530400" -I"$deps/final-ui-font")
clang++-18 "${flags[@]}" -std=c++20 -fno-exceptions -fno-rtti -c "$native/app_crt.cpp" -o "$work/start.o"
objects=("$work/start.o")
for source in console/ui/final_main.c console/ui/final_screen.c console/ui/screen.c console/ui/tiled_frame.c console/ui/assert_native.c console/vendor/qrcodegen.c console/worker/status_client.c; do
  object="$work/$(basename "$source").o"
  clang-18 "${flags[@]}" -std=c11 -c "$source" -o "$object"
  objects+=("$object")
done
"$sdk/bin/prospero-lld" -T "$native/ps5-pie.ld" --eh-frame-hdr -e _start -o "$work/llvm-pie.elf" "${objects[@]}" --as-needed "$sdk"/target/lib/*.so
"$tool" link --in "$work/llvm-pie.elf" --out "$work/eboot.elf" --stub-dir "$sdk/target/lib" --module-sdk 0x02000009 --companion-sdk 0x08050001 --file-name eboot.elf
title=artifacts/console/final-ui/PPSA99889
mkdir -p "$title/sce_sys" "$title/sce_module"
"$tool" self --sign --in "$work/eboot.elf" --out "$title/eboot.bin" --magic 0x1D3D154F
cp "$deps/title-build/libc.prx" "$title/sce_module/libc.prx"
test -s "$title/sce_sys/icon0.png"
"$tool" self --inspect --file "$title/eboot.bin"
python3 scripts/package-final-ui.py
