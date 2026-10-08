/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once
#include "https_result.h"
#include <stddef.h>
typedef struct { HttpsResult tls; int status; size_t size; } JsonResponse;
/* Fixed numeric endpoint, verified CA/name, bounded POST and Content-Length
 * response. No redirects, chunked fallback, cookies, logs or plaintext mode. */
JsonResponse https_json(const char *ip,unsigned short port,const char *name,
                        const char *ca,const char *path,const char *token,
                        const char *json,char *body,size_t capacity);
