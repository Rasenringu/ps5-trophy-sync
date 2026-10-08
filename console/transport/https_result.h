/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once
#include <stdint.h>
typedef struct {
    int rc;
    uint32_t verify_flags;
    int verified_handshake;
    int health_response;
    int connect_stage;
    int posix_errno;
} HttpsResult;
