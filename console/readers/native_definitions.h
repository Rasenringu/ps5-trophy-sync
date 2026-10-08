/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once
#include "ucp.h"
typedef struct { char id[257],name[801];char grade;int hidden; } NativeDefinition;
typedef struct { char npwr[13],language[16],title[801];unsigned count;NativeDefinition *trophies; } NativeDefinitions;
/* Definitions only. Never infer locked/unlocked from the configuration. */
int native_definitions(const Ucp *archive,NativeDefinitions *result);
void native_definitions_free(NativeDefinitions *result);
