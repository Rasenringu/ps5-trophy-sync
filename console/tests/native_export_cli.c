/* SPDX-License-Identifier: GPL-3.0-or-later */
#define main native_join_test_main
#include "native_join_cli.c"
#undef main
#include "../sync/native_export.h"
#include <string.h>
int main(int argc,char **argv){
    if(argc!=4)return 2;
    size_t ucp_size=0,state_size=0;
    unsigned char *ucp_bytes=load(argv[1],&ucp_size,64*1024*1024),*state_bytes=load(argv[2],&state_size,2*1024*1024);
    if(!ucp_bytes||!state_bytes){free(ucp_bytes);free(state_bytes);return 2;}
    Ucp ucp;NativeDefinitions defs={0};NativeState state={0};sqlite3 *db=NULL;int rc=2;
    if(ucp_validate(ucp_bytes,ucp_size,&ucp)||native_definitions(&ucp,&defs)||native_state_decode(state_bytes,state_size,&state)||native_export_prepare(&defs,&state,&db))goto done;
    for(unsigned first=0;first<state.count;first+=8){
        unsigned count=state.count-first;if(count>8)count=8;char json[8193];
        if(native_export_batch(db,"00000000-0000-4000-8000-000000000001",first,count,json))goto done;
        char filename[512];snprintf(filename,sizeof(filename),"%s-%u.json",argv[3],first);
        FILE *file=fopen(filename,"wb");if(!file)goto done;
        int bad=fwrite(json,1,strlen(json),file)!=strlen(json);if(fclose(file)||bad)goto done;
    }
    sqlite3_close(db);db=NULL;
    state.records[0].status=NATIVE_STATE_UNKNOWN;state.records[0].raw_flags=16;
    state.records[0].raw_time_first=0;state.records[0].raw_time_second=62135596800000001ULL;
    if(native_export_prepare(&defs,&state,&db))goto done;
    char json[8193];if(native_export_batch(db,"00000000-0000-4000-8000-000000000002",0,1,json))goto done;
    char filename[512];snprintf(filename,sizeof(filename),"%s-unknown.json",argv[3]);FILE *file=fopen(filename,"wb");if(!file)goto done;
    int bad=fwrite(json,1,strlen(json),file)!=strlen(json);if(fclose(file)||bad)goto done;
    if(!native_export_batch(db,"00000000-0000-4000-8000-000000000002",state.count,1,json))goto done;
    sqlite3_close(db);db=NULL;defs.trophies[1]=defs.trophies[0];
    if(!native_export_prepare(&defs,&state,&db))goto done;
    rc=0;
done:sqlite3_close(db);native_state_free(&state);native_definitions_free(&defs);free(ucp_bytes);free(state_bytes);return rc;
}
