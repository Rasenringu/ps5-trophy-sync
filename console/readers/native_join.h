/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once
#include "native_definitions.h"
#include "native_state.h"
typedef int (*NativeJoinedVisitor)(const NativeDefinition*,const NativeStateRecord*,void*);
/* Validate a one-to-one numeric ID mapping before any visitor runs. Definitions
 * can be reordered; unsupported/ambiguous IDs fail closed. UNKNOWN stays UNKNOWN.
 * No filesystem access, atomic snapshot guarantee or automatic import. */
int native_join(const NativeDefinitions*,const NativeState*,NativeJoinedVisitor,void*);
