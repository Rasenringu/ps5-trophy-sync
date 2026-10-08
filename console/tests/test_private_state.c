/* SPDX-License-Identifier: GPL-3.0-or-later */
#define _GNU_SOURCE 1
#include "../pairing/state.h"
#include <assert.h>
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>
#ifdef PS5_NATIVE_STATE
#include <sys/syscall.h>
static int forced_identity;
uid_t geteuid(void){
    if(forced_identity==1){errno=EPERM;return (uid_t)-1;}
    uid_t actual=(uid_t)syscall(SYS_geteuid);
    return forced_identity==2?actual+1:actual;
}
static int forced_sony_error;
int sceKernelMkdir(const char *path,unsigned mode){
    if(forced_sony_error)return forced_sony_error;
    return mkdir(path,mode)?(int)(0x80020000u|(unsigned)errno):0;
}
#endif
int main(void) {
    char root[]="/tmp/MOCK-state-XXXXXX";assert(mkdtemp(root));
    int dir=state_open(root);assert(dir>=0);
#ifdef PS5_NATIVE_STATE
    forced_sony_error=(int)0x80020001u;
    assert(state_open(root)==-1);
    assert(!strcmp(state_error_operation(),"Sony mkdir")&&state_error_code()==forced_sony_error);
    forced_sony_error=0;
    forced_identity=1;
    assert(state_open(root)==-1);
    assert(!strcmp(state_error_operation(),"effective UID query")&&state_error_code()==EPERM);
    assert(strstr(state_identity_evidence(),"EUID:denied e1"));
    forced_identity=2;
    assert(state_open(root)==-1);
    assert(!strcmp(state_error_operation(),"owner check")&&state_error_code()==EACCES);
    assert(!strstr(state_identity_evidence(),"Owner:self"));
    forced_identity=0;
#endif
    char output[8];const char value[8]="MOCK123";
    assert(state_read(dir,"state.bin",output,8)==1);
    assert(!state_write(dir,"state.bin",value,8));
    assert(!state_read(dir,"state.bin",output,8)&&!memcmp(value,output,8));
    assert(state_read(dir,"state.bin",output,7)==-1);
    assert(!strcmp(state_error_operation(),"file size")&&state_error_code()==EINVAL);
    assert(state_write(dir,"../other",value,8)==-1);
    assert(!symlinkat("state.bin",dir,"link.bin"));
    assert(state_read(dir,"link.bin",output,8)==-1);
    assert(!linkat(dir,"state.bin",dir,"hard.bin",0));
    assert(state_read(dir,"state.bin",output,8)==-1);
    assert(!unlinkat(dir,"hard.bin",0));
    assert(!fchmodat(dir,"state.bin",0644,0));
    assert(state_read(dir,"state.bin",output,8)==-1);
    int pending=openat(dir,".state.bin.new",O_WRONLY|O_CREAT|O_EXCL,0600);assert(pending>=0);close(pending);
    assert(state_write(dir,"state.bin",value,8)==-1);
    assert(!unlinkat(dir,".state.bin.new",0));
    assert(!unlinkat(dir,"link.bin",0));assert(!unlinkat(dir,"state.bin",0));
    assert(!fchmod(dir,0755));assert(state_open(root)==-1);
    assert(!strcmp(state_error_operation(),"mode check")&&state_error_code()==EACCES);
    close(dir);assert(!rmdir(root));
    puts("PASS LOCAL private state: exact size, owner/mode, symlink/hardlink refusal, unsafe names, interrupted save refusal.");
}
