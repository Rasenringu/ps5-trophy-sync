/* SPDX-License-Identifier: GPL-3.0-or-later */
#define _GNU_SOURCE 1
#define PS5_NATIVE_STATE 1
#define PS5_RESERVED_STATE 1
#include <assert.h>
#include <errno.h>
#include <fcntl.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>
static char parent[]="/tmp/MOCK-reserved-XXXXXX";
static char child[128];
static int deny_identity;
#ifdef PS5_WORKER_STATE
#define TEST_PARENT "/data"
#ifdef PS5_ENDPOINT_STATE
#include "probe_config.h"
#define TEST_DIRECTORY PROBE_STATE_DIRECTORY
#else
#define TEST_DIRECTORY "/data/trophy-sync-worker"
#endif
#define TEST_UID 0
#else
#define TEST_PARENT "/download0"
#define TEST_DIRECTORY "/download0/trophy-sync-live"
#define TEST_UID 1000
#endif
static uid_t fake_euid(void){if(deny_identity){errno=EPERM;return (uid_t)-1;}return TEST_UID;}
static uid_t fake_uid(void){return TEST_UID;}
static const char *mapped_path(const char *path,char buffer[256]){
    if(!strcmp(path,TEST_PARENT))return parent;
    const char *prefix=TEST_DIRECTORY;
    if(!strncmp(path,prefix,strlen(prefix))&&(path[strlen(prefix)]==0||path[strlen(prefix)]=='/')){
        snprintf(buffer,256,"%s%s",child,path+strlen(prefix));return buffer;
    }
    return path;
}
static int mapped_open(const char *path,int flags,...){
    mode_t mode=0;if(flags&O_CREAT){va_list args;va_start(args,flags);mode=(mode_t)va_arg(args,int);va_end(args);}
    char buffer[256];return open(mapped_path(path,buffer),flags,mode);
}
#ifdef PS5_ABSOLUTE_STATE
static int flushed,wrong_flushed_size;
static int mapped_fstat(int fd,struct stat *s){
    int rc=fstat(fd,s);
    if(!rc&&S_ISREG(s->st_mode)){
#ifdef PS5_ZERO_LINK_STATE
        if(s->st_nlink==1)s->st_nlink=0;
#endif
        if(!flushed)s->st_size=0;
        else if(wrong_flushed_size)s->st_size--;
    }
    return rc;
}
static int mapped_fsync(int fd){int rc=fsync(fd);if(!rc)flushed=1;return rc;}
static int mapped_rename(const char *from,const char *to){char a[256],b[256];return rename(mapped_path(from,a),mapped_path(to,b));}
static int mapped_unlink(const char *path){char buffer[256];return unlink(mapped_path(path,buffer));}
#define rename mapped_rename
#define unlink mapped_unlink
#define fstat mapped_fstat
#define fsync mapped_fsync
#endif
int sceKernelMkdir(const char *path,unsigned mode){
    const char *mapped=!strcmp(path,TEST_DIRECTORY)?child:path;
    return mkdir(mapped,mode)?(int)(0x80020000u|(unsigned)errno):0;
}
#define open mapped_open
#define geteuid fake_euid
#define getuid fake_uid
#include "../pairing/state.c"
#undef open
#undef geteuid
#undef getuid
#ifdef PS5_ABSOLUTE_STATE
#undef rename
#undef unlink
#undef fstat
#undef fsync
#endif
int main(void){
    assert(geteuid()==0); /* isolated root Docker fixture, never PS5. */
    assert(mkdtemp(parent));snprintf(child,sizeof(child),"%s/trophy-sync-live",parent);
    int dir=state_open(TEST_DIRECTORY);assert(dir>=0);
    char bytes[8],value[8]="MOCK123";
    assert(!state_write(dir,"state.bin",value,8));
    assert(!state_read(dir,"state.bin",bytes,8)&&!memcmp(bytes,value,8));
#ifdef PS5_ABSOLUTE_STATE
    wrong_flushed_size=1;
    assert(state_write(dir,"wrong.bin",value,8)==-1);
    assert(!strcmp(state_error_operation(),"file size"));
    assert(faccessat(dir,"wrong.bin",F_OK,0)==-1&&errno==ENOENT);
    wrong_flushed_size=0;
    char backup[160];snprintf(backup,sizeof(backup),"%s/moved",parent);
    assert(!rename(child,backup));assert(!mkdir(child,0700));
    assert(state_read(dir,"state.bin",bytes,8)==-1);
    assert(!strcmp(state_error_operation(),"reserved path changed"));
    assert(!rmdir(child));assert(!rename(backup,child));
#endif
    assert(!symlinkat("state.bin",dir,"link.bin"));
    assert(state_read(dir,"link.bin",bytes,8)==-1);
    assert(!linkat(dir,"state.bin",dir,"hard.bin",0));
    assert(state_read(dir,"state.bin",bytes,8)==-1);assert(!unlinkat(dir,"hard.bin",0));
    assert(!fchownat(dir,"state.bin",1001,0,0));
    assert(state_read(dir,"state.bin",bytes,8)==-1);
    assert(!strcmp(state_error_operation(),"owner check"));
    assert(!fchownat(dir,"state.bin",0,0,0));
    assert(!fchmodat(dir,"state.bin",0644,0));
    assert(state_read(dir,"state.bin",bytes,8)==-1);
    assert(!fchmodat(dir,"state.bin",0600,0));
    assert(state_read(dir,"state.bin",bytes,7)==-1);
    assert(!unlinkat(dir,"link.bin",0));assert(!unlinkat(dir,"state.bin",0));close(dir);
    deny_identity=1;assert(state_open(TEST_DIRECTORY)==-1);deny_identity=0;
    assert(state_open(child)==-1); /* root elsewhere is still rejected. */
    assert(!chmod(child,0755));assert(state_open(TEST_DIRECTORY)==-1);
    assert(!chmod(child,0700));assert(!chown(child,1001,0));
    assert(state_open(TEST_DIRECTORY)==-1);assert(!chown(child,0,0));
    assert(!chown(parent,1001,0));assert(state_open(TEST_DIRECTORY)==-1);
    assert(!chown(parent,0,0));
    dir=state_open(TEST_DIRECTORY);assert(dir>=0);close(dir);
    assert(!rmdir(child));assert(!rmdir(parent));
    puts("PASS MOCK reserved state: private writes/reloads; other paths/owners, denied identity, loose modes, reported multiple links and wrong sizes rejected. Zero link metadata, if enabled, does not prove no aliases.");
    return 0;
}
