/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once
#include <stddef.h>
#include <stdint.h>
enum { NATIVE_STATE_OK=0,NATIVE_STATE_FORMAT=1,NATIVE_STATE_BOUNDS=2,
       NATIVE_STATE_DIGEST=3,NATIVE_STATE_SCHEMA=4,NATIVE_STATE_MEMORY=5 };
typedef enum { NATIVE_STATE_UNKNOWN,NATIVE_STATE_LOCKED,NATIVE_STATE_EARNED } NativeStateStatus;
typedef struct {
    uint32_t id,raw_flags;
    NativeStateStatus status;
    uint64_t raw_time_first,raw_time_second;
    /* Candidate epoch interpretation corroborated by one console UI minute;
     * field distinction and clock accuracy remain unverified. Never manufacture
     * timestamps when either is absent or outside the representable range. */
    int64_t time_first_us,time_second_us;
    unsigned time_known;
} NativeStateRecord;
typedef struct {unsigned count;NativeStateRecord *records;} NativeState;
/* Observed native T2PD -> SHA256-protected pages -> T2TD directory schema.
 * Offline format decoder only: no filesystem access, snapshot/profile binding
 * or network imports. Unsupported flags stay UNKNOWN. Not a PS4 adapter. */
int native_state_decode(const unsigned char *bytes,size_t size,NativeState *result);
void native_state_free(NativeState *result);
