/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once
#include <stddef.h>
#include "native_collect.h"
typedef int (*NativeAssetVisitor)(sqlite3*,unsigned,const unsigned char*,size_t,const char*,void*);
/* Bounded exact NPWR discovery in the selected profile's observed native folder.
 * Equal same-FD reads and native integrity/join gates before a visitor. */
int native_collect_assets(unsigned,NativeCollected*,NativeAssetVisitor,void*);

typedef struct {unsigned found,missing,rejected;} NativeApplicationArtworkCounts;
typedef int (*NativeApplicationArtworkVisitor)(const unsigned char*,size_t,const char*,void*);
/* Exact logged application IDs only; observed appmeta/icon0.png source. */
int native_collect_application_artwork(unsigned profile,sqlite3 *activity,
    NativeApplicationArtworkCounts*,NativeApplicationArtworkVisitor,void*);
