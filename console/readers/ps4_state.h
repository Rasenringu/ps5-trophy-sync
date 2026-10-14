/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once
#include <stddef.h>
#include <stdint.h>
typedef struct {
    uint32_t id,grade,raw_state,raw_aux;
    uint64_t first_raw,second_raw;
    int unlocked; /* -1 unknown; 0 locked; 1 earned */
} Ps4StateRecord;
typedef struct {
    char title[13],applications[16][10];
    unsigned count,application_count;
    unsigned char package_sha1[20];
    Ps4StateRecord *records;
} Ps4State;
/* PS4 TRPTITLE index-table format, independently observed on FW8 copies.
 * Enforce both the embedded local profile and title identity. No filesystem,
 * mounts, source writes or PS5 state assumptions in this decoder. */
int ps4_state_decode(const unsigned char *bytes,size_t size,uint32_t profile,
                     const char *title,Ps4State *result);
void ps4_state_free(Ps4State *state);
