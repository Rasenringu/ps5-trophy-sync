/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "ps4_state.h"
#include <stdlib.h>
#include <string.h>
static uint32_t b32(const unsigned char *p){return (uint32_t)p[0]<<24|(uint32_t)p[1]<<16|(uint32_t)p[2]<<8|p[3];}
static uint64_t b64(const unsigned char *p){return (uint64_t)b32(p)<<32|b32(p+4);}
static int zero(const unsigned char *p,size_t n){for(size_t i=0;i<n;i++)if(p[i])return 0;return 1;}
typedef struct {uint32_t type,size,count;size_t offset,end;} Table;
static const unsigned char *record(const unsigned char *b,const Table *t,unsigned i){return b+t->offset+(size_t)i*(t->size+16)+16;}
void ps4_state_free(Ps4State *state){if(state){free(state->records);memset(state,0,sizeof(*state));}}
int ps4_state_decode(const unsigned char *b,size_t size,uint32_t profile,const char *title,Ps4State *out){
    if(!out)return 1;memset(out,0,sizeof(*out));
    if(!b||!title||strlen(title)!=12||strncmp(title,"NPWR",4)||strcmp(title+9,"_00")||size<48||size>2*1024*1024)return 1;
    for(unsigned i=4;i<9;i++)if(title[i]<'0'||title[i]>'9')return 1;
    if(b32(b)!=0x8d1f8d08||b32(b+4)!=0x10000||b32(b+8)!=10||!zero(b+12,36)||size<368)return 1;
    static const uint32_t types[10]={1,2,0x100,0x200,0x300,0x400,0x500,0x600,0x700,0x800};
    static const uint32_t lengths[10]={48,96,64,48,320,80,96,160,96,80};
    Table tables[10];size_t end=368;
    for(unsigned i=0;i<10;i++){
        const unsigned char *t=b+48+i*32;uint64_t offset=b64(t+16);uint32_t n=b32(t+12),length=b32(t+4);
        if(b32(t)!=types[i]||length!=lengths[i]||b32(t+8)!=1||!zero(t+24,8)||!n||n>2000||offset<end||offset>size||
           (uint64_t)n*(length+16)>size-offset)return 2;
        tables[i]=(Table){types[i],length,n,(size_t)offset,(size_t)offset+(size_t)n*(length+16)};
        if(!zero(b+end,(size_t)offset-end))return 2;
        for(unsigned j=0;j<n;j++){
            const unsigned char *h=b+offset+(size_t)j*(length+16);
            if(b32(h)!=types[i]||b32(h+4)!=length||!zero(h+8,8))return 2;
        }end=tables[i].end;
    }
    if(end!=size||tables[0].count!=1||tables[1].count!=1||tables[2].count!=1||tables[3].count!=16||
       tables[4].count!=1||tables[7].count!=1||tables[6].count!=tables[9].count)return 2;
    const unsigned char *identity=record(b,tables+1,0),*set=record(b,tables+4,0);
    if(b32(identity+40)!=profile||memcmp(set,title,12)||set[12]||memcmp(set+32,title,12)||set[44])return 3;
    memcpy(out->title,title,13);memcpy(out->package_sha1,record(b,tables+2,0),20);
    for(unsigned i=0;i<16;i++){
        const unsigned char *app=record(b,tables+3,i);if(!app[0])continue;
        if(memcmp(app,"CUSA",4)||memcmp(app+9,"_00",3)||app[12])goto invalid;
        for(unsigned j=4;j<9;j++)if(app[j]<'0'||app[j]>'9')goto invalid;
        for(unsigned j=0;j<out->application_count;j++)if(!memcmp(app,out->applications[j],9))goto invalid;
        memcpy(out->applications[out->application_count++],app,9);
    }
    out->count=tables[9].count;out->records=calloc(out->count,sizeof(*out->records));if(!out->records)goto invalid;
    for(unsigned i=0;i<out->count;i++){
        const unsigned char *definition=record(b,tables+6,i),*state=record(b,tables+9,i);
        if(b32(definition)!=i||b32(state)!=i||b32(definition+4)<1||b32(definition+4)>4||!zero(state+12,4)||!zero(state+32,48))goto invalid;
        Ps4StateRecord *r=out->records+i;r->id=i;r->grade=b32(definition+4);r->raw_state=b32(state+4);r->raw_aux=b32(state+8);
        r->first_raw=b64(state+16);r->second_raw=b64(state+24);r->unlocked=-1;
        if(!r->raw_state&&!r->raw_aux&&!r->first_raw&&!r->second_raw)r->unlocked=0;
        else if(r->raw_state==1&&r->raw_aux==0x2000)r->unlocked=1;
    }
    return 0;
invalid:ps4_state_free(out);return 4;
}
