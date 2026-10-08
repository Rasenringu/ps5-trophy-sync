/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "../readers/native_join.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static unsigned calls,unknown;
static int visit(const NativeDefinition *d,const NativeStateRecord *s,void *context){
    (void)context;calls++;if(s->status==NATIVE_STATE_UNKNOWN)unknown++;
    if(s->id==0)assert(d->grade=='B');else assert(d->grade=='G');return 0;
}
int main(void){
    NativeDefinition rows[2]={{.id="0001",.grade='G'},{.id="0000",.grade='B'}};
    NativeStateRecord states[2]={{.id=0,.status=NATIVE_STATE_EARNED},{.id=1,.status=NATIVE_STATE_UNKNOWN}};
    NativeDefinitions defs={.count=2,.trophies=rows};NativeState state={.count=2,.records=states};
    assert(!native_join(&defs,&state,visit,NULL));assert(calls==2&&unknown==1);
    const char *bad[]={"1","0001","-1","+1","0x1","1 ","42949672960","2",""};
    for(unsigned n=0;n<sizeof(bad)/sizeof(bad[0]);n++){
        strcpy(rows[1].id,bad[n]);calls=0;assert(native_join(&defs,&state,visit,NULL));assert(!calls);
    }
    strcpy(rows[1].id,"0000");state.count=1;assert(native_join(&defs,&state,visit,NULL));assert(!calls);
    state.count=2;states[0].id=1;assert(native_join(&defs,&state,visit,NULL));assert(!calls);
    puts("PASS MOCK native join: reordered definitions, unknown preserved, duplicate numeric IDs/overflow/missing/mismatch reject before any output.");
    return 0;
}
