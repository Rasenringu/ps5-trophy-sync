/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "screen.h"
#include <stdio.h>
#include <string.h>
#include <ctype.h>
#include <limits.h>
static bool origin_valid(const char *s) {
    if (!s || strncmp(s, "https://", 8) || !s[8] || strlen(s) >= 192) return false;
    /* Intentionally conservative hostname[:port], no userinfo/path/query/fragment. */
    const char *colon = NULL;
    for (const char *p = s + 8; *p; p++) {
        if (*p == ':') { if (colon) return false; colon = p; }
        else if (!(isalnum((unsigned char)*p) || *p == '-' || *p == '.')) return false;
    }
    size_t hostlen = colon ? (size_t)(colon - s - 8) : strlen(s + 8);
    if (!hostlen || s[8] == '.' || s[8] == '-' || s[8 + hostlen - 1] == '.' || s[8 + hostlen - 1] == '-') return false;
    if (colon) {
        unsigned port = 0;
        if (!colon[1]) return false;
        for (const char *p = colon + 1; *p; p++) {
            if (!isdigit((unsigned char)*p)) return false;
            port = port * 10 + (unsigned)(*p - '0');
            if (port > 65535) return false;
        }
        if (!port) return false;
    }
    return true;
}
bool ui_set_pairing(UiModel *m, const char *origin, const char *code, uint64_t now, unsigned ttl) {
    /* Clear stale authorization before validating a replacement. */
    m->phase = UI_UNAVAILABLE; m->manual_code[0] = 0; m->public_origin[0] = 0; m->expires_at_ms = 0;
    if (!origin_valid(origin) || !code || strlen(code) != 9 || code[4] != '-' || !ttl || ttl > 600 || now > UINT64_MAX - (uint64_t)ttl * 1000) return false;
    for (int i = 0; i < 9; i++) if (i != 4 && !((code[i] >= 'A' && code[i] <= 'Z') || (code[i] >= '2' && code[i] <= '9'))) return false;
    snprintf(m->public_origin, sizeof(m->public_origin), "%s", origin);
    snprintf(m->manual_code, sizeof(m->manual_code), "%s", code);
    m->expires_at_ms = now + (uint64_t)ttl * 1000; m->phase = UI_PAIRING;
    return true;
}
bool ui_pairing_link(const UiModel *m, uint64_t now, char *out, unsigned cap) {
    if (cap) out[0] = 0;
    if (m->phase != UI_PAIRING || now >= m->expires_at_ms ||
        !memchr(m->public_origin, 0, sizeof(m->public_origin)) ||
        m->manual_code[9] != 0 || strlen(m->manual_code) != 9 || m->manual_code[4] != '-' ||
        !origin_valid(m->public_origin)) return false;
    for (int i = 0; i < 9; i++) if (i != 4 && !((m->manual_code[i] >= 'A' && m->manual_code[i] <= 'Z') || (m->manual_code[i] >= '2' && m->manual_code[i] <= '9'))) return false;
    int n = snprintf(out, cap, "%s/pair?code=%s", m->public_origin, m->manual_code);
    if (n < 0 || (unsigned)n >= cap) { if (cap) out[0] = 0; return false; }
    return true;
}
