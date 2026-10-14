/* SPDX-License-Identifier: GPL-3.0-or-later */
/* MOCK kernel/mount/decoder interfaces; real private snapshot and collector.
 * No console contact. Decoder format is independently tested by ps4-state. */
#define _GNU_SOURCE
#include <assert.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dirent.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/ioctl.h>
#include <unistd.h>
#include <mbedtls/sha1.h>
#include "../sync/ps4_collect.h"
static char root[128];
static uint64_t auth=42;
static uint8_t capabilities[16];
static unsigned visits,mounts,unmounts;
static int failure;
static const char *mapped(const char *path,char out[512]){
    assert(path[0]=='/');assert(snprintf(out,512,"%s%s",root,path)<512);return out;
}
static int test_open(const char *path,int flags,...){
    mode_t mode=0;if(flags&O_CREAT){va_list a;va_start(a,flags);mode=(mode_t)va_arg(a,int);va_end(a);}
    if(!strncmp(path,"/user/",6))assert((flags&O_ACCMODE)==O_RDONLY&&!(flags&O_CREAT));
    char p[512];return open(mapped(path,p),flags,mode);
}
static DIR *test_opendir(const char *path){char p[512];return opendir(mapped(path,p));}
static int test_mkdir(const char *path,mode_t mode){assert(!strncmp(path,"/data/trophy-sync-ps4-reader",27));char p[512];return mkdir(mapped(path,p),mode);}
static int test_rmdir(const char *path){assert(!strncmp(path,"/data/trophy-sync-ps4-reader",27));char p[512];return rmdir(mapped(path,p));}
static int test_unlink(const char *path){assert(!strcmp(path,"/data/trophy-sync-ps4-reader/image"));char p[512];return unlink(mapped(path,p));}
static int test_ioctl(int fd,unsigned long request,void *key){(void)fd;assert(request==0xc0845302UL&&auth==0x4800000000000010ULL);memset((char*)key+96,7,32);return failure==1?-1:0;}
#define open test_open
#define opendir test_opendir
#define mkdir test_mkdir
#define rmdir test_rmdir
#define unlink test_unlink
#define ioctl test_ioctl
#include "../sync/ps4_collect.c"
#undef open
#undef opendir
#undef mkdir
#undef rmdir
#undef unlink
#undef ioctl
uint64_t kernel_get_ucred_authid(pid_t p){assert(p==getpid());return auth;}
int kernel_set_ucred_authid(pid_t p,uint64_t a){assert(p==getpid());auth=a;return 0;}
int kernel_get_ucred_caps(pid_t p,uint8_t *c){assert(p==getpid());memcpy(c,capabilities,16);return 0;}
int kernel_set_ucred_caps(pid_t p,const uint8_t *c){assert(p==getpid());memcpy(capabilities,c,16);return 0;}
uintptr_t kernel_dynlib_dlsym(int p,uint32_t h,const char *n){(void)p;(void)h;(void)n;assert(0);return 0;}
int sceUserServiceGetForegroundUser(uint32_t *p){*p=failure==4&&mounts?2:1;return 0;}
static void put(const char *path,const void *b,size_t n){char p[512];mapped(path,p);int fd=open(p,O_WRONLY|O_CREAT|O_EXCL,0600);assert(fd>=0&&write(fd,b,n)==(ssize_t)n);close(fd);}
static int mock_init(MountOpt *o){(void)o;return 0;}
static int mock_init_end(UnmountOpt *o){(void)o;return 0;}
static int mock_mount(MountOpt *o,const char *image,const char *mount,uint8_t *key){
    assert(!strcmp(image,STAGE "/image")&&!strcmp(mount,STAGE "/mount")&&!strcmp(o->budgetid,"system"));
    assert(auth==0x4800000000000010ULL&&key[0]==7);for(unsigned i=0;i<16;i++)assert(capabilities[i]==255);
    mounts++;unsigned char state[96]={0};put(STAGE "/mount/TRPTITLE.DAT",state,sizeof(state));return 1;
}
static int mock_end(UnmountOpt *o,const char *mount,int h,int force){
    (void)o;assert(!strcmp(mount,STAGE "/mount")&&h==1&&!force);unmounts++;
    if(failure==2)return -99;
    char p[512];assert(!unlink(mapped(STAGE "/mount/TRPTITLE.DAT",p)));return 0;
}
static unsigned char package[96];
int ps4_state_decode(const unsigned char *b,size_t n,uint32_t p,const char *t,Ps4State *s){
    (void)b;assert(n==96&&p==1&&!strcmp(t,"NPWR00001_00"));
    if(failure==3)return 1;
    strcpy(s->title,t);memcpy(s->package_sha1,package+28,20);s->count=1;s->records=calloc(1,sizeof(*s->records));assert(s->records);return 0;
}
void ps4_state_free(Ps4State *s){free(s->records);memset(s,0,sizeof(*s));}
static int visit(const Ps4State *s,const unsigned char *b,size_t n,void *c){
    (void)c;assert(s->count==1&&n==96&&!memcmp(b,package,96)&&auth==42);for(unsigned i=0;i<16;i++)assert(!capabilities[i]);visits++;return failure==5?-1:0;
}
static void folder(const char *path){char p[512];mapped(path,p);assert(!mkdir(p,0700));}
int main(void){
    strcpy(root,"/tmp/ps4-collector-XXXXXX");assert(mkdtemp(root));
    const char *dirs[]={"/user","/user/home","/user/home/00000001","/user/home/00000001/trophy","/user/home/00000001/trophy/data","/user/home/00000001/trophy/data/NPWR00001_00","/user/trophy","/user/trophy/conf","/user/trophy/conf/NPWR00001_00","/data","/dev"};
    for(unsigned i=0;i<sizeof(dirs)/sizeof(*dirs);i++)folder(dirs[i]);
    unsigned char image[1024]={1};uint64_t magic=20130315;memcpy(image+8,&magic,8);
    put("/user/home/00000001/trophy/data/NPWR00001_00/trophy.img",image,sizeof(image));
    unsigned char key[96]="pfsSKKey";put("/user/home/00000001/trophy/data/NPWR00001_00/sealedkey",key,96);
    memcpy(package,"\xdc\xa2\x4d\0\0\0\0\3",8);unsigned char sha[20];assert(!mbedtls_sha1(package,96,sha));memcpy(package+28,sha,20);
    put("/user/trophy/conf/NPWR00001_00/TROPHY.TRP",package,96);put("/dev/pfsmgr","",0);
    init_mount=mock_init;mount_copy=mock_mount;init_unmount=mock_init_end;unmount_copy=mock_end;
    for(failure=0;failure<=5;failure++){
        visits=mounts=unmounts=0;Ps4Collected count;int rc=ps4_collect(1,&count,visit,NULL);
        assert(auth==42);for(unsigned j=0;j<16;j++)assert(!capabilities[j]);
        assert(visits==(failure==0||failure==5));
        if(!failure)assert(!rc&&count.sets==1);
        else if(failure==3)assert(!rc&&count.rejected==1);
        else assert(rc<0);
        char p[512];int fd=open(mapped("/user/home/00000001/trophy/data/NPWR00001_00/trophy.img",p),O_RDONLY);unsigned char current[1024];assert(fd>=0&&read(fd,current,1024)==1024&&!memcmp(image,current,1024));close(fd);
        if(failure==2){assert(count.stage==6);assert(!access(mapped(STAGE "/image",p),F_OK));Ps4Collected again;assert(ps4_collect(1,&again,visit,NULL)<0&&again.stage==8);assert(!unlink(mapped(STAGE "/mount/TRPTITLE.DAT",p)));assert(!rmdir(mapped(STAGE "/mount",p)));assert(!unlink(mapped(STAGE "/image",p)));assert(!rmdir(mapped(STAGE,p)));}
    }
    char p[512];const char *files[]={"/user/home/00000001/trophy/data/NPWR00001_00/trophy.img","/user/home/00000001/trophy/data/NPWR00001_00/sealedkey","/user/trophy/conf/NPWR00001_00/TROPHY.TRP","/dev/pfsmgr"};
    for(unsigned i=0;i<4;i++)assert(!unlink(mapped(files[i],p)));
    for(unsigned i=sizeof(dirs)/sizeof(*dirs);i>0;i--)assert(!rmdir(mapped(dirs[i-1],p)));assert(!rmdir(root));
    puts("PASS MOCK PS4 collector: private-copy-only mounts, unchanged source, credential restore before visitor, unseal/decode/profile/visitor/unmount failure and preserved busy staging");return 0;
}
