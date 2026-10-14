/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once
#include "../readers/ps4_state.h"
#include <sqlite3.h>
int ps4_export_prepare(const Ps4State *state,sqlite3 **output);
int ps4_export_batch(sqlite3 *db,const char *uuid,unsigned first,unsigned count,char output[8193]);
