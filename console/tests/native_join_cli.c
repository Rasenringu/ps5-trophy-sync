/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "../readers/native_join.h"
#include <stdio.h>
#include <stdlib.h>
typedef struct {unsigned earned,locked,unknown,bronze,silver,gold,platinum;} Counts;
static unsigned char *load(const char *name,size_t *size,long bound){
    FILE *f=fopen(name,"rb");if(!f)return NULL;
    if(fseek(f,0,SEEK_END)){fclose(f);return NULL;}long n=ftell(f);
    if(n<64||n>bound||fseek(f,0,SEEK_SET)){fclose(f);return NULL;}
    unsigned char *b=malloc((size_t)n);if(!b){fclose(f);return NULL;}
    if(fread(b,1,(size_t)n,f)!=(size_t)n){free(b);fclose(f);return NULL;}
    fclose(f);*size=(size_t)n;return b;
}
static int visit(const NativeDefinition *d,const NativeStateRecord *s,void *context){
    Counts *c=context;
    if(s->status==NATIVE_STATE_LOCKED)c->locked++;
    else if(s->status==NATIVE_STATE_UNKNOWN)c->unknown++;
    else{c->earned++;switch(d->grade){case 'B':c->bronze++;break;case 'S':c->silver++;break;case 'G':c->gold++;break;case 'P':c->platinum++;break;}}
    return 0;
}
int main(int argc,char **argv){
    if(argc!=3)return 2;
    size_t ucp_size=0,state_size=0;
    unsigned char *ucp_bytes=load(argv[1],&ucp_size,64*1024*1024),*state_bytes=load(argv[2],&state_size,2*1024*1024);
    if(!ucp_bytes||!state_bytes){free(ucp_bytes);free(state_bytes);return 2;}
    Ucp ucp;NativeDefinitions defs={0};NativeState state={0};Counts counts={0};
    int rc=ucp_validate(ucp_bytes,ucp_size,&ucp)||native_definitions(&ucp,&defs)||native_state_decode(state_bytes,state_size,&state)||native_join(&defs,&state,visit,&counts);
    printf("{\"rc\":%d,\"earned\":%u,\"locked\":%u,\"unknown\":%u,\"bronze\":%u,\"silver\":%u,\"gold\":%u,\"platinum\":%u}\n",rc,counts.earned,counts.locked,counts.unknown,counts.bronze,counts.silver,counts.gold,counts.platinum);
    native_state_free(&state);native_definitions_free(&defs);free(ucp_bytes);free(state_bytes);return 0;
}
