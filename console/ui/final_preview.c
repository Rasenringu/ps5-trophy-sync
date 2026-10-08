/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Explicit offline synthetic states. Never contacts a console or server. */
#include "final_screen.h"
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
int main(int argc,char **argv){
    if(argc!=3)return 2;
    UiModel m={.mock=true,.close_with_shell=true};uint64_t now=1000;
    snprintf(m.profile,sizeof(m.profile),"Profil de démonstration");
    if(!ui_set_pairing(&m,"https://example.invalid","DEMO-2345",0,300))return 3;
    if(!strcmp(argv[1],"expired"))now=300000;
    else if(!strcmp(argv[1],"connected")){m.phase=UI_CONNECTED;snprintf(m.sync_status,sizeof(m.sync_status),"Sync complete: 2 batches. 0 missing / 0 rejected sets");snprintf(m.reader_status,sizeof(m.reader_status),"Native: 8 sets; playtime 7 complete / 0 incomplete");}
    else if(!strcmp(argv[1],"syncing")){m.phase=UI_CONNECTED;snprintf(m.error,sizeof(m.error),"Reading native game foreground sessions...");}
    else if(!strcmp(argv[1],"partial")){m.phase=UI_CONNECTED;snprintf(m.sync_status,sizeof(m.sync_status),"Sync complete: 2 batches. 1 missing / 2 rejected sets");}
    else if(!strcmp(argv[1],"connecting"))m.phase=UI_UNAVAILABLE;
    else if(!strcmp(argv[1],"error")){m.phase=UI_ERROR;snprintf(m.error,sizeof(m.error),"Enable FTP2121 v0.21.1 for trophy discovery (-101)");snprintf(m.sync_status,sizeof(m.sync_status),"Sync failed: native sources unavailable");}
    else if(!strcmp(argv[1],"long")){m.phase=UI_ERROR;memset(m.error,'W',sizeof(m.error));memset(m.reader_status,'W',sizeof(m.reader_status));memset(m.sync_status,'W',sizeof(m.sync_status));memset(m.profile,'W',sizeof(m.profile));}
    uint32_t *pixels=malloc((size_t)SCREEN_WIDTH*SCREEN_HEIGHT*4);if(!pixels)return 4;
    ui_render_final(pixels,&m,now);
    FILE *f=fopen(argv[2],"wb");if(!f){free(pixels);return 5;}
    fprintf(f,"P6\n%d %d\n255\n",SCREEN_WIDTH,SCREEN_HEIGHT);
    for(int i=0;i<SCREEN_WIDTH*SCREEN_HEIGHT;i++){unsigned char rgb[]={pixels[i]>>16,pixels[i]>>8,pixels[i]};if(fwrite(rgb,1,3,f)!=3){fclose(f);free(pixels);return 6;}}
    free(pixels);return fclose(f)?7:0;
}
