/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "ps4_collect.h"
#include "../readers/ps4_image_snapshot.h"
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <mbedtls/platform_util.h>
#include <mbedtls/sha1.h>
#include <ps5/kernel.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/stat.h>
#include <unistd.h>
#define STAGE "/data/trophy-sync-ps4-reader"
typedef struct {uint8_t reserved;char *budgetid;} MountOpt;
typedef struct {uint8_t dummy;} UnmountOpt;
typedef struct {uint64_t authid;uint8_t caps[16];int active;} CredentialGuard;
static int (*init_mount)(MountOpt*);
static int (*mount_copy)(MountOpt*,const char*,const char*,uint8_t*);
static int (*init_unmount)(UnmountOpt*);
static int (*unmount_copy)(UnmountOpt*,const char*,int,int);
extern int sceUserServiceGetForegroundUser(uint32_t*);
static int same_user(uint32_t profile){uint32_t p=UINT32_MAX;return !sceUserServiceGetForegroundUser(&p)&&p==profile;}
static int title_ok(const char *n){if(strlen(n)!=12||strncmp(n,"NPWR",4)||strcmp(n+9,"_00"))return 0;for(int i=4;i<9;i++)if(n[i]<'0'||n[i]>'9')return 0;return 1;}
static int guard_end(CredentialGuard *g){
    if(!g->active)return 0;int caps=kernel_set_ucred_caps(getpid(),g->caps),auth=kernel_set_ucred_authid(getpid(),g->authid);
    g->active=0;mbedtls_platform_zeroize(g,sizeof(*g));return caps||auth?-1:0;
}
static int guard_begin(CredentialGuard *g){
    memset(g,0,sizeof(*g));g->authid=kernel_get_ucred_authid(getpid());
    if(!g->authid||kernel_get_ucred_caps(getpid(),g->caps))return -1;
    g->active=1;
    if(kernel_set_ucred_authid(getpid(),0x4800000000000010ULL))return -1;
    uint8_t caps[16];memset(caps,255,sizeof(caps));int rc=kernel_set_ucred_caps(getpid(),caps);mbedtls_platform_zeroize(caps,sizeof(caps));
    /* Keep guard active on setup failure: the caller checks restoration too. */
    if(rc)return -1;return 0;
}
static int load_fs(void){
    if(init_mount&&mount_copy&&init_unmount&&unmount_copy)return 0;
    int (*load)(const char*,size_t,const void*,unsigned,void*,int*)=(void*)kernel_dynlib_dlsym(-1,1,"sceKernelLoadStartModule");
    if(!load)load=(void*)kernel_dynlib_dlsym(-1,0x2001,"sceKernelLoadStartModule");if(!load)return -1;
    int h=load("/system/priv/lib/libSceFsInternalForVsh.sprx",0,NULL,0,NULL,NULL);if(h<0)return h;
    init_mount=(void*)kernel_dynlib_dlsym(-1,(uint32_t)h,"sceFsInitMountTrophyDataOpt");
    mount_copy=(void*)kernel_dynlib_dlsym(-1,(uint32_t)h,"sceFsMountTrophyData");
    init_unmount=(void*)kernel_dynlib_dlsym(-1,(uint32_t)h,"sceFsInitUmountTrophyDataOpt");
    unmount_copy=(void*)kernel_dynlib_dlsym(-1,(uint32_t)h,"sceFsUmountTrophyData");
    return init_mount&&mount_copy&&init_unmount&&unmount_copy?0:-1;
}
static int take(int fd,unsigned char *p,size_t n,off_t at){size_t used=0;while(used<n){ssize_t k=pread(fd,p+used,n-used,at+(off_t)used);if(k<=0)return -1;used+=(size_t)k;}return 0;}
static int equal(const struct stat *a,const struct stat *b){return a->st_dev==b->st_dev&&a->st_ino==b->st_ino&&a->st_size==b->st_size&&a->st_mtime==b->st_mtime&&a->st_ctime==b->st_ctime;}
static unsigned char *stable_read(const char *path,size_t bound,size_t *size){
    int fd=open(path,O_RDONLY|O_NOFOLLOW|O_CLOEXEC|O_NONBLOCK);if(fd<0)return NULL;
    struct stat before,after;unsigned char *bytes=NULL,chunk[65536];
    if(fstat(fd,&before))goto done;
    if(!S_ISREG(before.st_mode)||before.st_size<96||(uint64_t)before.st_size>bound){errno=EINVAL;goto done;}
    *size=(size_t)before.st_size;bytes=malloc(*size);if(!bytes||take(fd,bytes,*size,0))goto bad;
    for(size_t at=0;at<*size;){size_t n=*size-at;if(n>sizeof(chunk))n=sizeof(chunk);if(take(fd,chunk,n,(off_t)at)||memcmp(bytes+at,chunk,n))goto bad;at+=n;}
    if(fstat(fd,&after)||!equal(&before,&after))goto bad;goto done;
bad:free(bytes);bytes=NULL;errno=EIO;
done:close(fd);return bytes;
}
static int one(uint32_t profile,const char *title,Ps4Collected *counts,Ps4Visitor visitor,void *context){
    char original[256],keypath[256],packagepath[256];
    snprintf(original,sizeof(original),"/user/home/%08x/trophy/data/%s/trophy.img",profile,title);
    snprintf(keypath,sizeof(keypath),"/user/home/%08x/trophy/data/%s/sealedkey",profile,title);
    snprintf(packagepath,sizeof(packagepath),"/user/trophy/conf/%s/TROPHY.TRP",title);
    size_t package_size=0,state_size=0;unsigned char *package=NULL,*state_bytes=NULL;
    Ps4State state={0};CredentialGuard guard={0};int result=-1,mounted=0,handle=-1,have_copy=0,have_mountdir=0,rc=0;
    uint8_t key[132]={0},second[96]={0};
    counts->stage=3;rc=guard_begin(&guard);if(rc)goto done;
    package=stable_read(packagepath,32*1024*1024,&package_size);
    if(!package){
        if(errno==ENOENT){counts->missing++;result=0;}else counts->stage=10;
        goto done;
    }
    if(memcmp(package,"\xdc\xa2\x4d\0\0\0\0\3",8)){counts->rejected++;result=0;goto done;}
    unsigned char digest[20],zero[20]={0};mbedtls_sha1_context sha;mbedtls_sha1_init(&sha);
    rc=mbedtls_sha1_starts(&sha);if(!rc)rc=mbedtls_sha1_update(&sha,package,28);if(!rc)rc=mbedtls_sha1_update(&sha,zero,20);
    if(!rc)rc=mbedtls_sha1_update(&sha,package+48,package_size-48);if(!rc)rc=mbedtls_sha1_finish(&sha,digest);mbedtls_sha1_free(&sha);
    if(rc||memcmp(digest,package+28,20)){counts->rejected++;result=0;goto done;}
    counts->stage=1;
    int source=open(original,O_RDONLY|O_NOFOLLOW|O_CLOEXEC),copy=open(STAGE "/image",O_RDWR|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC,0600);
    if(copy>=0)have_copy=1;
    if(source<0||copy<0){if(source>=0)close(source);if(copy>=0)close(copy);goto done;}
    rc=ps4_image_snapshot(source,copy,32*1024*1024);close(source);close(copy);if(rc)goto done;
    if(!same_user(profile)){result=-2;goto done;}
    counts->stage=2;int keyfd=open(keypath,O_RDONLY|O_NOFOLLOW|O_CLOEXEC);struct stat key_stat;
    if(keyfd<0)goto done;
    int valid=!fstat(keyfd,&key_stat)&&S_ISREG(key_stat.st_mode)&&key_stat.st_size==96&&
        !take(keyfd,key,96,0)&&!take(keyfd,second,96,0)&&!memcmp(key,second,96)&&!memcmp(key,"pfsSKKey",8);
    close(keyfd);if(!valid)goto done;
    counts->stage=3;rc=load_fs();if(rc)goto done;
    int manager=open("/dev/pfsmgr",O_RDWR|O_CLOEXEC);if(manager<0)goto done;
    rc=ioctl(manager,0xc0845302UL,key);close(manager);if(rc)goto done;
    if(!same_user(profile)){result=-2;goto done;}
    counts->stage=4;if(mkdir(STAGE "/mount",0700))goto done;have_mountdir=1;
    MountOpt opt={0};rc=init_mount(&opt);opt.budgetid="system";if(rc)goto done;
    /* Mount path and volume path are fixed OWN private paths, never originals. */
    handle=mount_copy(&opt,STAGE "/image",STAGE "/mount",key+96);if(handle<0){rc=handle;goto done;}mounted=1;
    mbedtls_platform_zeroize(key,sizeof(key));mbedtls_platform_zeroize(second,sizeof(second));
    counts->stage=5;state_bytes=stable_read(STAGE "/mount/TRPTITLE.DAT",2*1024*1024,&state_size);if(!state_bytes)goto done;
    rc=ps4_state_decode(state_bytes,state_size,profile,title,&state);
    if(rc||memcmp(state.package_sha1,package+28,20)){counts->rejected++;ps4_state_free(&state);result=0;goto done;}
    if(!same_user(profile)){result=-2;goto done;}result=0;
done:
    counts->rc=rc;counts->error=errno;
    if(mounted){UnmountOpt opt={0};int end=init_unmount(&opt);if(!end)end=unmount_copy(&opt,STAGE "/mount",handle,0);if(end){counts->stage=6;counts->rc=end;result=-3;}else mounted=0;}
    if(guard_end(&guard)){counts->stage=7;result=-4;}
    mbedtls_platform_zeroize(key,sizeof(key));mbedtls_platform_zeroize(second,sizeof(second));
    if(!mounted){if(have_mountdir)rmdir(STAGE "/mount");if(have_copy)unlink(STAGE "/image");}
    if(!result&&state.records){
        if(!same_user(profile))result=-2;
        else if(visitor(&state,package,package_size,context))result=-5;
        else{counts->sets++;for(unsigned i=0;i<state.count;i++){counts->earned+=state.records[i].unlocked==1;counts->locked+=state.records[i].unlocked==0;counts->unknown+=state.records[i].unlocked==-1;}}
    }
    ps4_state_free(&state);free(state_bytes);free(package);return result;
}
int ps4_collect(uint32_t profile,Ps4Collected *counts,Ps4Visitor visitor,void *context){
    if(!counts||!visitor)return -1;memset(counts,0,sizeof(*counts));
    if(!same_user(profile))return -2;
    /* The dedicated FS privilege is also required for protected source reads.
     * Enumerate under our own guard, restore, then guard each private snapshot.
     * No visitor/network can execute while this guard is active. */
    CredentialGuard guard={0};char names[128][13],root[128];unsigned seen=0;int rc=0;
    counts->stage=3;rc=guard_begin(&guard);
    DIR *dir=NULL;
    if(!rc){snprintf(root,sizeof(root),"/user/home/%08x/trophy/data",profile);dir=opendir(root);
        if(!dir){counts->error=errno;counts->stage=10;if(errno==ENOENT)counts->missing++;else rc=-1;}
    }
    if(dir){struct dirent *entry;
        while((entry=readdir(dir))){if(!title_ok(entry->d_name))continue;if(seen==128){rc=-1;counts->stage=9;break;}
            if(!same_user(profile)){rc=-2;break;}memcpy(names[seen++],entry->d_name,13);
        }
        closedir(dir);
    }
    if(guard_end(&guard)){counts->stage=7;return -4;}
    if(rc||!seen)return rc;
    if(mkdir(STAGE,0700)){counts->stage=8;counts->error=errno;return -1;}
    for(unsigned i=0;i<seen;i++){
        if(!same_user(profile)){rc=-2;break;}
        rc=one(profile,names[i],counts,visitor,context);if(rc)break;
    }
    rmdir(STAGE);return rc;
}
