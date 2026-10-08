/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once
#include <stddef.h>
#include <stdint.h>
enum { UCP_OK=0,UCP_FORMAT=1,UCP_BOUNDS=2,UCP_DIGEST=3,UCP_NAMES=4,UCP_MEMORY=5 };
typedef struct { const unsigned char *bytes;size_t size;uint32_t count; } Ucp;
typedef struct { char name[33];const unsigned char *bytes;size_t size; } UcpEntry;
/* Buffer stays owned by caller; no extraction/filesystem writes. */
int ucp_validate(const unsigned char *bytes,size_t size,Ucp *result);
int ucp_entry(const Ucp *archive,uint32_t index,UcpEntry *result);
int ucp_find(const Ucp *archive,const char *name,UcpEntry *result);
