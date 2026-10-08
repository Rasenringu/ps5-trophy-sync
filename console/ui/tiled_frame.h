/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once
#include <stddef.h>
#include <stdint.h>
#define DIRECT_FRAME_BYTES 0x1000000u
#define DIRECT_POOL_BYTES (2u * DIRECT_FRAME_BYTES)
size_t ui_tiled_offset(unsigned x, unsigned y);
void ui_tile_frame(void *destination, const uint32_t *argb);
