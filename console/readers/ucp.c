/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Format reference: SvenGDK/LibProsperoPKG commit 748eabf1b7d17819528cabf367d8e27109d8fce3.
 * Independent bounded reader; actual native capture matched header/table/digest.
 * Container definitions do not establish profile unlock state. */
#include "ucp.h"
#include <mbedtls/sha1.h>
#include <stdlib.h>
#include <string.h>
static uint32_t be32(const unsigned char *p) { return (uint32_t)p[0]<<24 | (uint32_t)p[1]<<16 | (uint32_t)p[2]<<8 | p[3]; }
static uint64_t be64(const unsigned char *p) { return (uint64_t)be32(p)<<32 | be32(p+4); }
typedef struct { char name[33];size_t offset,size; } Range;
static int names(const void *a,const void *b) { return strcmp(((const Range*)a)->name,((const Range*)b)->name); }
static int offsets(const void *a,const void *b) {
    const Range *x=a,*y=b;
    if(x->offset!=y->offset) return x->offset<y->offset ? -1 : 1;
    return x->size<y->size ? -1 : x->size>y->size;
}
int ucp_validate(const unsigned char *bytes,size_t size,Ucp *result) {
    if (!result) return UCP_FORMAT;
    memset(result,0,sizeof(*result));
    if (!bytes || size<96 || size>64u*1024*1024) return UCP_BOUNDS;
    if (be32(bytes)!=0xb228c60a || be32(bytes+4)!=1 || be32(bytes+20)!=64) return UCP_FORMAT;
    uint32_t count=be32(bytes+16);
    if (be64(bytes+8)!=size || count>4096 || count>(size-96)/64) return UCP_BOUNDS;
    size_t table_end=96+(size_t)count*64;
    Range *ranges=count ? calloc(count,sizeof(*ranges)) : NULL;
    if(count && !ranges) return UCP_MEMORY;
    int rc=UCP_OK;
    for (uint32_t i=0;i<count;i++) {
        const unsigned char *record=bytes+96+(size_t)i*64;
        size_t length=0;
        while(length<32 && record[length]) {
            if(record[length]<32 || record[length]>126 || record[length]=='/' || record[length]=='\\') { rc=UCP_NAMES;goto done; }
            length++;
        }
        if(!length || (length==1 && record[0]=='.') || (length==2 && record[0]=='.' && record[1]=='.')) { rc=UCP_NAMES;goto done; }
        for(size_t n=length;n<32;n++) if(record[n]) { rc=UCP_NAMES;goto done; }
        uint64_t offset=be64(record+32),length64=be64(record+40);
        if(offset<table_end || offset>size || length64>size-offset) { rc=UCP_BOUNDS;goto done; }
        memcpy(ranges[i].name,record,length);
        ranges[i].offset=(size_t)offset;ranges[i].size=(size_t)length64;
    }
    if(count) {
        qsort(ranges,count,sizeof(*ranges),names);
        for(uint32_t i=1;i<count;i++) if(!strcmp(ranges[i-1].name,ranges[i].name)) { rc=UCP_NAMES;goto done; }
        qsort(ranges,count,sizeof(*ranges),offsets);
        size_t end=table_end;
        for(uint32_t i=0;i<count;i++) if(ranges[i].size) {
            if(ranges[i].offset<end) { rc=UCP_BOUNDS;goto done; }
            end=ranges[i].offset+ranges[i].size;
        }
    }
    mbedtls_sha1_context hash;mbedtls_sha1_init(&hash);
    unsigned char digest[20],zero[20]={0};
    int error=mbedtls_sha1_starts(&hash);
    if(!error) error=mbedtls_sha1_update(&hash,bytes,28);
    if(!error) error=mbedtls_sha1_update(&hash,zero,sizeof(zero));
    if(!error) error=mbedtls_sha1_update(&hash,bytes+48,size-48);
    if(!error) error=mbedtls_sha1_finish(&hash,digest);
    mbedtls_sha1_free(&hash);
    if(error || memcmp(digest,bytes+28,20)) { rc=UCP_DIGEST;goto done; }
    *result=(Ucp){.bytes=bytes,.size=size,.count=count};
done:
    free(ranges);return rc;
}
int ucp_entry(const Ucp *archive,uint32_t index,UcpEntry *result) {
    if(!archive || !archive->bytes || !result || index>=archive->count) return UCP_BOUNDS;
    const unsigned char *record=archive->bytes+96+(size_t)index*64;
    memset(result,0,sizeof(*result));memcpy(result->name,record,32);
    result->bytes=archive->bytes+(size_t)be64(record+32);result->size=(size_t)be64(record+40);
    return UCP_OK;
}
int ucp_find(const Ucp *archive,const char *name,UcpEntry *result) {
    if(!archive || !name || !result) return UCP_BOUNDS;
    for(uint32_t i=0;i<archive->count;i++) {
        UcpEntry entry;if(ucp_entry(archive,i,&entry)) return UCP_BOUNDS;
        if(!strcmp(entry.name,name)) { *result=entry;return UCP_OK; }
    }
    return UCP_NAMES;
}
