/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once
#include "../readers/native_join.h"
#include <sqlite3.h>
/* In-memory DTO serialization only. No filesystem/network/credentials.
 * Validate the entire ID join before serialization. Unknown state stays null;
 * both raw times retained; candidate first time labeled uncertain. */
int native_export_prepare(const NativeDefinitions*,const NativeState*,sqlite3**);
int native_export_batch(sqlite3*,const char *batch_uuid,unsigned first,unsigned count,char output[8193]);
