/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "../readers/ps4_state.h"
#include <stdio.h>
#include <stdlib.h>
#ifdef PS4_EXPORT_CLI
#include "../sync/ps4_export.h"
#endif
int main(int argc,char **argv){
    if(argc!=4)return 2;FILE *f=fopen(argv[1],"rb");if(!f)return 2;fseek(f,0,SEEK_END);long n=ftell(f);rewind(f);
    if(n<0||n>2*1024*1024){fclose(f);return 2;}unsigned char *b=malloc((size_t)n);if(!b){fclose(f);return 2;}
    if(fread(b,1,(size_t)n,f)!=(size_t)n){free(b);fclose(f);return 2;}fclose(f);Ps4State state;
    int rc=ps4_state_decode(b,(size_t)n,(uint32_t)strtoul(argv[2],NULL,16),argv[3],&state);free(b);
    if(rc){printf("rejected=%d\n",rc);return 1;}unsigned earned=0,locked=0,unknown=0;
#ifdef PS4_EXPORT_CLI
    sqlite3 *db=NULL;if(ps4_export_prepare(&state,&db)){ps4_state_free(&state);return 1;}
    puts("[");
    for(unsigned first=0;first<state.count;){
        unsigned count=state.count-first;if(count>8)count=8;char json[8193];
        if(ps4_export_batch(db,"00000000-0000-4000-8000-000000000001",first,count,json)){sqlite3_close(db);ps4_state_free(&state);return 1;}
        if(first)puts(",");puts(json);first+=count;
    }
    puts("]");sqlite3_close(db);ps4_state_free(&state);return 0;
#endif
    for(unsigned i=0;i<state.count;i++){earned+=state.records[i].unlocked==1;locked+=state.records[i].unlocked==0;unknown+=state.records[i].unlocked==-1;}
    printf("title=%s count=%u earned=%u locked=%u unknown=%u applications=%u\n",state.title,state.count,earned,locked,unknown,state.application_count);ps4_state_free(&state);return 0;
}
