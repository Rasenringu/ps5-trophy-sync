#!/usr/bin/env bash
# Source-built native FSELF tooling and runtime; no proprietary module copied.
set -euo pipefail
cd /workspace
python3 scripts/prepare-title-deps.py
deps=/workspace/.local/console-build
native="$deps/ps5-native-app-boilerplate-2f672d1c2f508e26f82ce6e27cef289a0861413c/tooling/native"
work="$deps/title-build"
mkdir -p "$work"
cmake -S "$deps/zlib-1.3.2" -B "$deps/zlib-host-build" -DCMAKE_BUILD_TYPE=Release >"$work/build.log" 2>&1
cmake --build "$deps/zlib-host-build" -j4 >>"$work/build.log" 2>&1
clang++-18 -std=c++20 -O2 -I"$deps/zlib-1.3.2" -I"$deps/zlib-host-build" \
  "$native/native_app_builder.cpp" "$native/self_container.cpp" "$native/elf_object.cpp" \
  "$native/sce_module_writer.cpp" "$deps/zlib-host-build/libz.a" -o "$work/native-tool"
clang++-18 -std=c++20 -O2 "$native/libc_builder.cpp" -o "$work/libc-builder"
"$work/libc-builder" "$native/runtime/api-surface.txt" "$native/runtime/imports.txt" "$work/libc.raw.elf"
printf '%s  %s\n' 8ee6e124993e1af26420cb455890fd002f5d6c7e78883c860ce45734e7d002bb "$work/libc.raw.elf" | sha256sum -c -
"$work/native-tool" self --sign --in "$work/libc.raw.elf" --out "$work/libc.prx"
printf '%s  %s\n' e6ff45d16adf687855cc3b33b0c8a4132b6504360b221e0a34c7e99fb3ba0036 "$work/libc.prx" | sha256sum -c -
