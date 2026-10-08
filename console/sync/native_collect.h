/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once
#include <sqlite3.h>
typedef struct {unsigned sets,earned,locked,unknown,missing,rejected;} NativeCollected;
typedef int (*NativeCollectionVisitor)(sqlite3*,unsigned,void*);
/* Actual observed native candidates only. O_RDONLY, bounded same-FD equal reads,
 * metadata and per-page digest checks. Not an atomic generation guarantee.
 * Verify foreground profile before/after every source and before each visitor. */
int native_collect(unsigned profile,NativeCollected*,NativeCollectionVisitor,void*);
