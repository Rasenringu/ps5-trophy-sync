/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once
#include <sqlite3.h>
typedef struct {unsigned rows,sessions,completed,incomplete,rejected;} NativeActivityCounts;
/* Uses the existing write-blocking SQLite VFS and platform shared locks. Output
 * is private memory only. Does not perform network I/O or mutate source files. */
int native_activity_collect(const char *path,unsigned profile,sqlite3 **output,NativeActivityCounts *counts);
int native_activity_batch(sqlite3 *memory,const char *uuid,unsigned first,unsigned count,char output[8193]);
