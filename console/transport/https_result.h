/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once
#include <stdint.h>
enum { HTTPS_PHASE_NONE, HTTPS_PHASE_HANDSHAKE, HTTPS_PHASE_REQUEST_HEADERS,
       HTTPS_PHASE_UPLOAD, HTTPS_PHASE_RESPONSE_HEADERS, HTTPS_PHASE_RESPONSE_BODY,
       HTTPS_PHASE_COMPLETE };
typedef struct {
    int rc;
    uint32_t verify_flags;
    int verified_handshake;
    int health_response;
    int connect_stage;
    int posix_errno;
    unsigned phase;
    uint64_t bytes_sent,payload_size;
} HttpsResult;
