/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once
#include <stdbool.h>
#include <stdint.h>
#define SCREEN_WIDTH 1920
#define SCREEN_HEIGHT 1080
typedef enum { UI_UNAVAILABLE, UI_PAIRING, UI_CONNECTED, UI_ERROR, UI_DIAGNOSTIC } UiPhase;
typedef struct {
    UiPhase phase;
    bool mock;
    bool close_with_shell;
    char profile[64];
    /* Display model deliberately has no installation/device credential fields. */
    char public_origin[192];
    char manual_code[10];
    uint64_t expires_at_ms;
    char error[160];
    char reader_status[160];
    char sync_status[160];
} UiModel;
/* Accepts only an HTTPS origin and ABCD-2345 code, never an arbitrary QR URL. */
bool ui_set_pairing(UiModel *m, const char *origin, const char *code,
                    uint64_t now_ms, unsigned ttl_seconds);
bool ui_pairing_link(const UiModel *m, uint64_t now_ms, char *out, unsigned capacity);
