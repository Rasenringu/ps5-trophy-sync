/* Tiled address calculation adapted from BlackBearReloaded's native template.
 * Copyright (C) 2026 BlackBearReloaded
 * Integration: PS5 Trophy Sync contributors
 * SPDX-License-Identifier: GPL-3.0-or-later
 * Source pin: 2f672d1c2f508e26f82ce6e27cef289a0861413c, demo_renderer.cpp.
 */
#include "tiled_frame.h"
#include "screen.h"
size_t ui_tiled_offset(unsigned x, unsigned y) {
    uint32_t offset = ((y << 4) & 0x70u) ^ ((y << 5) & 0xf00u) ^ ((y << 9) & 0x1000u) ^
                      ((y << 8) & 0x4000u) ^ ((x << 2) & 0xcu) ^ ((x << 5) & 0x380u) ^
                      ((x << 4) & 0x400u) ^ ((x << 6) & 0x800u) ^ ((x << 9) & 0xa000u);
    unsigned blocks = (SCREEN_WIDTH + 127u) >> 7;
    return ((size_t)((y >> 7) * blocks + (x >> 7)) << 16) + offset;
}
void ui_tile_frame(void *destination, const uint32_t *argb) {
    uint8_t *bytes = destination;
    for (unsigned y = 0; y < SCREEN_HEIGHT; y++) for (unsigned x = 0; x < SCREEN_WIDTH; x++) {
        uint32_t c = argb[y * SCREEN_WIDTH + x];
        /* Renderer ARGB words -> VideoOut ABGR words; preserve alpha/green. */
        uint32_t abgr = (c & 0xff00ff00u) | ((c & 0xffu) << 16) | ((c >> 16) & 0xffu);
        *(uint32_t *)(bytes + ui_tiled_offset(x, y)) = abgr;
    }
}
