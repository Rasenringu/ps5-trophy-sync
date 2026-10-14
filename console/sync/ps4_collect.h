/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once
#include "../readers/ps4_state.h"
typedef struct {unsigned sets,earned,locked,unknown,missing,rejected;int stage,rc,error;} Ps4Collected;
typedef int (*Ps4Visitor)(const Ps4State*,const unsigned char*,size_t,void*);
/* Read originals; mount ONLY verified disposable copies, unmount and restore
 * this process's credentials before any visitor/network operation. No copy-back. */
int ps4_collect(uint32_t profile,Ps4Collected *counts,Ps4Visitor visitor,void *context);
