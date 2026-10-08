/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "../ui/tiled_frame.h"
#include "../ui/screen.h"
#include <assert.h>
#include <stdlib.h>
#include <stdio.h>
int main(void) {
    uint8_t *seen = calloc(DIRECT_FRAME_BYTES/4,1);
    uint32_t *linear = malloc((size_t)SCREEN_WIDTH*SCREEN_HEIGHT*4);
    uint8_t *tiled = calloc(DIRECT_FRAME_BYTES,1);
    assert(seen && linear && tiled);
    for (unsigned y=0;y<SCREEN_HEIGHT;y++) for (unsigned x=0;x<SCREEN_WIDTH;x++) {
        size_t offset = ui_tiled_offset(x,y);
        assert(offset%4==0 && offset+4<=DIRECT_FRAME_BYTES && !seen[offset/4]);
        seen[offset/4]=1;
        linear[y*SCREEN_WIDTH+x] = 0xff000000u | (x%256)<<16 | (y%256)<<8 | ((x+y)%256);
    }
    ui_tile_frame(tiled,linear);
    for (unsigned y=0;y<SCREEN_HEIGHT;y++) for (unsigned x=0;x<SCREEN_WIDTH;x++) {
        uint32_t c=*(uint32_t*)(tiled+ui_tiled_offset(x,y));
        assert(c==(0xff000000u | ((x+y)%256)<<16 | (y%256)<<8 | (x%256)));
    }
    free(seen); free(linear); free(tiled);
    puts("PASS: all 1920x1080 tiled addresses aligned, unique, in bounds; pixel channels preserved");
}
