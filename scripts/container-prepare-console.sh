#!/usr/bin/env bash
# Prepare only dependencies used by the current worker; never execute a payload.
set -euo pipefail
cd /workspace
python3 scripts/prepare-probe-deps.py
python3 scripts/prepare-probe-config.py
deps=/workspace/.local/console-build
mkdir -p "$deps/probe-build"
source /opt/ps5-payload-sdk/toolchain/prospero.sh
"$CMAKE" -S "$deps/mbedtls-3.6.7" -B "$deps/mbedtls-ps5-build" \
  -DCMAKE_BUILD_TYPE=Release -DENABLE_TESTING=OFF -DENABLE_PROGRAMS=OFF \
  -DCMAKE_INSTALL_PREFIX="$deps/probe-ps5" >"$deps/tls-build.log" 2>&1
if ! cmake --build "$deps/mbedtls-ps5-build" -j4 >>"$deps/tls-build.log" 2>&1; then tail -40 "$deps/tls-build.log"; exit 1; fi
env -u DESTDIR cmake --install "$deps/mbedtls-ps5-build" >>"$deps/tls-build.log" 2>&1
sqlite_flags=(-DSQLITE_THREADSAFE=0 -DSQLITE_OMIT_WAL -DSQLITE_OMIT_LOAD_EXTENSION
  -DSQLITE_OMIT_SHARED_CACHE -DSQLITE_TEMP_STORE=3 -DSQLITE_MAX_MMAP_SIZE=0)
"$CC" -O2 "${sqlite_flags[@]}" -c "$deps/sqlite-amalgamation-3530400/sqlite3.c" -o "$deps/probe-build/sqlite3.o"
make -B -C console build/crt-readonly.o
if [[ "${1:-}" == --host-tests ]]; then
  cmake -S "$deps/mbedtls-3.6.7" -B "$deps/mbedtls-host-linux-build" \
    -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=/usr/bin/cc -DCMAKE_CXX_COMPILER=/usr/bin/c++ \
    -DENABLE_TESTING=OFF -DENABLE_PROGRAMS=OFF >"$deps/tls-host-build.log" 2>&1
  if ! cmake --build "$deps/mbedtls-host-linux-build" -j4 >>"$deps/tls-host-build.log" 2>&1; then tail -40 "$deps/tls-host-build.log"; exit 1; fi
  cc -O2 "${sqlite_flags[@]}" -c "$deps/sqlite-amalgamation-3530400/sqlite3.c" -o "$deps/probe-build/sqlite3-host.o"
fi
