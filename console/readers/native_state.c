/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "native_state.h"
#include <mbedtls/sha256.h>
#include <stdlib.h>
#include <string.h>
static uint32_t be32(const unsigned char *p){return (uint32_t)p[0]<<24|(uint32_t)p[1]<<16|(uint32_t)p[2]<<8|p[3];}
static uint64_t be64(const unsigned char *p){return (uint64_t)be32(p)<<32|be32(p+4);}
static int zero(const unsigned char *p,size_t n){for(size_t i=0;i<n;i++)if(p[i])return 0;return 1;}
static unsigned time_value(uint64_t raw,int64_t *value){
    const uint64_t epoch=UINT64_C(62135596800000000),max=UINT64_C(253402300799999999);
    if(raw<epoch||raw-epoch>max)return 0;
    *value=(int64_t)(raw-epoch);return 1;
}
void native_state_free(NativeState *result){if(result){free(result->records);memset(result,0,sizeof(*result));}}
int native_state_decode(const unsigned char *bytes,size_t size,NativeState *result){
    if(!result)return NATIVE_STATE_FORMAT;
    memset(result,0,sizeof(*result));
    if(!bytes||size<64||size>2u*1024*1024)return NATIVE_STATE_BOUNDS;
    if(memcmp(bytes,"T2PD",4)||be32(bytes+4)!=0x10000||be64(bytes+8)!=1056||
       !zero(bytes+16,16)||!zero(bytes+40,24))return NATIVE_STATE_FORMAT;
    uint64_t pages=be64(bytes+32);
    if(!pages||pages>1024||64+pages*1056!=size)return NATIVE_STATE_BOUNDS;
    size_t logical_size=(size_t)pages*1024;
    unsigned char *logical=malloc(logical_size);if(!logical)return NATIVE_STATE_MEMORY;
    int rc=NATIVE_STATE_FORMAT;
    for(size_t page=0;page<(size_t)pages;page++){
        const unsigned char *source=bytes+64+page*1056;unsigned char digest[32];
        if(mbedtls_sha256(source,1024,digest,0)||memcmp(digest,source+1024,32)){rc=NATIVE_STATE_DIGEST;goto done;}
        memcpy(logical+page*1024,source,1024);
    }
    if(logical_size<48||memcmp(logical,"T2TD",4)||be32(logical+4)!=0x10000||!zero(logical+12,36))goto done;
    uint32_t entries=be32(logical+8);
    if(!entries||entries>64||entries>(logical_size-48)/32){rc=NATIVE_STATE_BOUNDS;goto done;}
    size_t end=48+(size_t)entries*32,state_offset=0,definition_offset=0;
    uint32_t count=0,definition_count=0,previous_tag=0;
    for(uint32_t i=0;i<entries;i++){
        const unsigned char *entry=logical+48+(size_t)i*32;
        uint32_t tag=be32(entry),payload=be32(entry+4),version=be32(entry+8),repeat=be32(entry+12);
        uint64_t offset=be64(entry+16);
        if(!tag||(i&&tag<=previous_tag)||version!=1||be64(entry+24)||!repeat||repeat>4096){rc=NATIVE_STATE_SCHEMA;goto done;}
        previous_tag=tag;
        if(payload>logical_size||offset!=end||offset>logical_size||repeat>(logical_size-(size_t)offset)/((size_t)payload+16)){
            rc=NATIVE_STATE_BOUNDS;goto done;
        }
        size_t stride=(size_t)payload+16;
        for(uint32_t n=0;n<repeat;n++){
            const unsigned char *record=logical+(size_t)offset+(size_t)n*stride;
            if(be32(record)!=tag||be32(record+4)!=payload||be64(record+8)){rc=NATIVE_STATE_SCHEMA;goto done;}
        }
        if(tag==0x500){if(payload!=192){rc=NATIVE_STATE_SCHEMA;goto done;}definition_offset=(size_t)offset;definition_count=repeat;}
        if(tag==0x800){if(payload!=80){rc=NATIVE_STATE_SCHEMA;goto done;}state_offset=(size_t)offset;count=repeat;}
        end=(size_t)offset+stride*repeat;
    }
    if(!count||count!=definition_count||!zero(logical+end,logical_size-end)){rc=NATIVE_STATE_SCHEMA;goto done;}
    result->records=calloc(count,sizeof(*result->records));if(!result->records){rc=NATIVE_STATE_MEMORY;goto done;}
    result->count=count;
    for(uint32_t n=0;n<count;n++){
        const unsigned char *record=logical+state_offset+(size_t)n*96+16;
        const unsigned char *definition=logical+definition_offset+(size_t)n*208+16;
        NativeStateRecord *out=result->records+n;
        out->id=be32(record);out->raw_flags=be32(record+4);
        if(out->id!=n||be32(definition)!=out->id){rc=NATIVE_STATE_SCHEMA;goto done;}
        out->raw_time_first=be64(record+16);out->raw_time_second=be64(record+32);
        out->time_known=time_value(out->raw_time_first,&out->time_first_us)|time_value(out->raw_time_second,&out->time_second_us)<<1;
        if(!out->raw_flags&&!out->raw_time_first&&!out->raw_time_second)out->status=NATIVE_STATE_LOCKED;
        else if(out->raw_flags==17&&out->time_known==3)out->status=NATIVE_STATE_EARNED;
        else out->status=NATIVE_STATE_UNKNOWN;
    }
    rc=NATIVE_STATE_OK;
done:
    free(logical);if(rc)native_state_free(result);return rc;
}
