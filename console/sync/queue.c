/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "queue.h"
#include "../pairing/state.h"
#include <mbedtls/sha256.h>
#include <stdio.h>
#include <string.h>
static void filename(char out[64],unsigned profile,unsigned slot){snprintf(out,64,"queue-%08x-%02u.bin",profile,slot);}
static int seal(SyncQueueItem *item){
    memset(item->digest,0,sizeof(item->digest));unsigned char hash[32];
    if(mbedtls_sha256((const unsigned char*)item,sizeof(*item),hash,0))return -1;
    memcpy(item->digest,hash,32);return 0;
}
int sync_queue_load(int directory,unsigned profile,unsigned slot,const char *installation,
                    const char *profile_uuid,const char *origin,SyncQueueItem *item){
    if(!item||slot>=SYNC_QUEUE_SLOTS)return -1;
    char name[64];filename(name,profile,slot);
    int rc=state_read(directory,name,item,sizeof(*item));if(rc)return rc;
    if(memcmp(item->magic,"PS5Q2\0\0",8)||item->version!=2||item->acknowledged>1||item->profile!=profile||
       item->length==0||item->length>8192||item->json[item->length]||strlen(item->json)!=item->length||
       !memchr(item->installation,0,37)||!memchr(item->profile_uuid,0,37)||!memchr(item->origin,0,192)||
       strcmp(item->installation,installation)||strcmp(item->profile_uuid,profile_uuid)||strcmp(item->origin,origin))return -1;
    unsigned char before[32];memcpy(before,item->digest,32);
    if(seal(item)||memcmp(before,item->digest,32))return -1;
    return 0;
}
int sync_queue_put(int directory,unsigned profile,const char *installation,
                   const char *profile_uuid,const char *origin,const char *json,unsigned *slot){
    if(!installation||strlen(installation)!=36||!profile_uuid||strlen(profile_uuid)!=36||
       !origin||strlen(origin)>=192||!json||!*json||strlen(json)>8192||!slot)return -1;
    SyncQueueItem item;
    for(unsigned n=0;n<SYNC_QUEUE_SLOTS;n++){
        int rc=sync_queue_load(directory,profile,n,installation,profile_uuid,origin,&item);
        if(rc<0)return -1;
        if(rc==1||item.acknowledged){
            memset(&item,0,sizeof(item));memcpy(item.magic,"PS5Q2\0\0",8);item.version=2;item.profile=profile;
            snprintf(item.installation,sizeof(item.installation),"%s",installation);
            snprintf(item.profile_uuid,sizeof(item.profile_uuid),"%s",profile_uuid);
            snprintf(item.origin,sizeof(item.origin),"%s",origin);item.length=(unsigned)strlen(json);
            memcpy(item.json,json,item.length+1);char name[64];filename(name,profile,n);
            if(seal(&item)||state_write(directory,name,&item,sizeof(item)))return -1;
            *slot=n;return 0;
        }
    }
    return -2; /* Bounded queue full: retain all pending data. */
}
int sync_queue_ack(int directory,unsigned slot,SyncQueueItem *item){
    if(!item||slot>=SYNC_QUEUE_SLOTS)return -1;
    item->acknowledged=1;char name[64];filename(name,item->profile,slot);
    if(seal(item))return -1;
    return state_write(directory,name,item,sizeof(*item));
}
