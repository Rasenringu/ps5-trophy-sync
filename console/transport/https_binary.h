/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once
#include "https_json.h"
/* Same validated TLS endpoint policy, bounded public native package payload. */
JsonResponse https_binary(const char *ip,unsigned short port,const char *name,
 const char *ca,const char *path,const char *token,const unsigned char *payload,
 size_t payload_size,char *body,size_t capacity);
