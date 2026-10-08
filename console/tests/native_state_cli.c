/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Host-only private fixture CLI. No console or network operations. */
#include "../readers/native_state.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <inttypes.h>
int main(int argc,char **argv){
    if(argc<2)return 2;
    FILE *file=fopen(argv[1],"rb");if(!file)return 2;
    if(fseek(file,0,SEEK_END)){fclose(file);return 2;}
    long size=ftell(file);if(size<0||size>2*1024*1024||fseek(file,0,SEEK_SET)){fclose(file);return 2;}
    unsigned char *bytes=malloc(size?(size_t)size:1);if(!bytes){fclose(file);return 2;}
    if(fread(bytes,1,(size_t)size,file)!=(size_t)size){fclose(file);free(bytes);return 2;}fclose(file);
    NativeState state;int rc=native_state_decode(bytes,(size_t)size,&state);free(bytes);
    unsigned earned=0,locked=0,unknown=0;
    for(unsigned i=0;i<state.count;i++){earned+=state.records[i].status==NATIVE_STATE_EARNED;
        locked+=state.records[i].status==NATIVE_STATE_LOCKED;unknown+=state.records[i].status==NATIVE_STATE_UNKNOWN;}
    printf("{\"rc\":%d,\"count\":%u,\"earned\":%u,\"locked\":%u,\"unknown\":%u",rc,state.count,earned,locked,unknown);
    if(argc==3&&!strcmp(argv[2],"--details")){
        printf(",\"records\":[");
        for(unsigned i=0;i<state.count;i++){
            NativeStateRecord *r=state.records+i;
            printf("%s{\"id\":%u,\"flags\":%u,\"status\":%d,\"time_known\":%u,\"first_us\":%" PRId64 ",\"second_us\":%" PRId64 "}",
                i?",":"",r->id,r->raw_flags,r->status,r->time_known,r->time_first_us,r->time_second_us);
        }
        printf("]");
    }
    puts("}");native_state_free(&state);return 0;
}
