/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "native_collect_assets.h"
#include "native_export.h"
#include "native_discovery_ftp.h"
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>
extern int sceUserServiceGetForegroundUser(uint32_t*);
static int same_user(unsigned profile){uint32_t current=UINT32_MAX;return !sceUserServiceGetForegroundUser(&current)&&current==profile;}
static int same(const struct stat *a,const struct stat *b){return a->st_dev==b->st_dev&&a->st_ino==b->st_ino&&a->st_size==b->st_size&&a->st_mtime==b->st_mtime;}
static int read_all(int fd,unsigned char *bytes,size_t size){
    size_t used=0;while(used<size){size_t next=size-used;if(next>65536)next=65536;ssize_t n=read(fd,bytes+used,next);if(n<=0)return 0;used+=(size_t)n;}return 1;
}
static unsigned char *stable_read(const char *path,size_t limit,size_t *size,int *missing){
    *missing=0;int fd=open(path,O_RDONLY|O_NOFOLLOW|O_CLOEXEC);if(fd<0){*missing=1;return NULL;}
    struct stat before,middle,after;unsigned char *first=NULL,*second=NULL;
    if(fstat(fd,&before)||!S_ISREG(before.st_mode)||before.st_size<64||(uint64_t)before.st_size>limit)goto done;
    *size=(size_t)before.st_size;first=malloc(*size);second=malloc(*size);
    if(!first||!second||!read_all(fd,first,*size)||fstat(fd,&middle)||!same(&before,&middle)||lseek(fd,0,SEEK_SET)!=0||
       !read_all(fd,second,*size)||fstat(fd,&after)||!same(&before,&after)||memcmp(first,second,*size)){
        free(first);first=NULL;
    }
done:free(second);close(fd);return first;
}
int native_collect_assets(unsigned profile,NativeCollected *counts,NativeAssetVisitor visitor,void *context){
    if(!counts||!visitor)return -1;
    memset(counts,0,sizeof(*counts));
    char candidates[128][13];unsigned sets=0;
    int discovery=native_discover(profile,candidates,&sets);if(discovery)return -100+discovery;
    for(unsigned i=0;i<sets;i++){
        if(!same_user(profile))return -2;
        const char *name=candidates[i];
        char path[256];snprintf(path,sizeof(path),"/user/home/%08x/trophy2/nobackup/data/%s/TRPTITLE.DAT",profile,name);
        size_t state_size=0,ucp_size=0;int missing=0;
        unsigned char *state_bytes=stable_read(path,2*1024*1024,&state_size,&missing);
        if(!state_bytes){if(missing)counts->missing++;else counts->rejected++;continue;}
        NativeState state={0};NativeDefinitions definitions={0};sqlite3 *exported=NULL;unsigned char *ucp_bytes=NULL;
        int rc=-1;
        if(native_state_decode(state_bytes,state_size,&state))goto cleanup;
        snprintf(path,sizeof(path),"/user/trophy2/nobackup/conf/%s/TROPHY.UCP",name);
        ucp_bytes=stable_read(path,64*1024*1024,&ucp_size,&missing);Ucp ucp;
        if(!ucp_bytes||ucp_validate(ucp_bytes,ucp_size,&ucp)||native_definitions(&ucp,&definitions)||strcmp(definitions.npwr,name)||native_export_prepare(&definitions,&state,&exported))goto cleanup;
        if(!same_user(profile)){rc=-2;goto cleanup;}
        if(visitor(exported,state.count,ucp_bytes,ucp_size,name,context)){rc=-3;goto cleanup;}
        counts->sets++;
        for(unsigned n=0;n<state.count;n++){
            if(state.records[n].status==NATIVE_STATE_EARNED)counts->earned++;
            else if(state.records[n].status==NATIVE_STATE_LOCKED)counts->locked++;else counts->unknown++;
        }
        rc=0;
cleanup:
        sqlite3_close(exported);native_definitions_free(&definitions);native_state_free(&state);free(ucp_bytes);free(state_bytes);
        if(rc==-2||rc==-3)return rc;
        if(rc)counts->rejected++;
    }
    return same_user(profile)?0:-2;
}
