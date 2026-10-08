/* SPDX-License-Identifier: GPL-3.0-or-later */
#define _POSIX_C_SOURCE 200809L
#include "native_join.h"
#include <stdlib.h>
#include <string.h>
static int numeric_id(const char *text,unsigned count,unsigned *id){
    size_t length=strnlen(text,257);if(!length||length>10)return 0;
    unsigned value=0;
    for(size_t n=0;n<length;n++){
        if(text[n]<'0'||text[n]>'9')return 0;
        unsigned digit=(unsigned)(text[n]-'0');
        if(value>(UINT32_MAX-digit)/10)return 0;
        value=value*10+digit;
    }
    if(value>=count)return 0;
    *id=value;
    return 1;
}
int native_join(const NativeDefinitions *defs,const NativeState *state,NativeJoinedVisitor visitor,void *context){
    if(!defs||!state||!visitor||!defs->trophies||!state->records||!defs->count||defs->count>1000||defs->count!=state->count)return 1;
    const NativeDefinition **mapped=calloc(state->count,sizeof(*mapped));if(!mapped)return 2;
    int rc=1;
    for(unsigned n=0;n<defs->count;n++){
        unsigned id;if(!numeric_id(defs->trophies[n].id,state->count,&id)||mapped[id]||state->records[id].id!=id)goto done;
        mapped[id]=defs->trophies+n;
    }
    for(unsigned id=0;id<state->count;id++)if(!mapped[id])goto done;
    rc=0;
    for(unsigned id=0;id<state->count;id++)if(visitor(mapped[id],state->records+id,context)){rc=3;break;}
done:free(mapped);return rc;
}
