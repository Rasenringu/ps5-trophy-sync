/* SPDX-License-Identifier: GPL-3.0-or-later */
#define _GNU_SOURCE 1
#include "state.h"
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>
#ifdef PS5_WORKER_STATE
#define PRIVATE_STATE_BASE "/data/trophy-sync-worker"
#define PRIVATE_STATE_PARENT "/data"
#define PRIVATE_STATE_LIMIT 16384
#else
#define PRIVATE_STATE_BASE "/download0/trophy-sync-live"
#define PRIVATE_STATE_PARENT "/download0"
#define PRIVATE_STATE_LIMIT 4096
#endif
static const char *failure_operation="unknown";
static int failure_code;
static char identity_evidence[160];
static void (*state_progress_hook)(unsigned);
void state_set_progress(void (*progress)(unsigned stage)){state_progress_hook=progress;}
static void state_progress(unsigned stage){if(state_progress_hook)state_progress_hook(stage);}
#ifdef PS5_RESERVED_STATE
/* One pairing/console worker. Pin the validated private directory descriptor
 * and inode; the reserved ownership policy never applies to other paths. */
static int reserved_fd=-1;
static dev_t reserved_device;
static ino_t reserved_inode;
static int reserved_context(int dir){
    struct stat s={0};
    return dir==reserved_fd&&!fstat(dir,&s)&&S_ISDIR(s.st_mode)&&s.st_uid==0&&
        !(s.st_mode&0077)&&s.st_dev==reserved_device&&s.st_ino==reserved_inode;
}
#endif
const char *state_identity_evidence(void){return identity_evidence;}
const char *state_error_operation(void){return failure_operation;}
int state_error_code(void){return failure_code;}
static int failed(const char *operation,int code){failure_operation=operation;failure_code=code?code:EIO;return -1;}
#ifdef PS5_NATIVE_STATE
extern int sceKernelMkdir(const char *,unsigned);
static int make_directory(const char *path){
    int rc=sceKernelMkdir(path,0700);
    if(!rc)return 0;
    if(((unsigned)rc&0xffff0000u)==0x80020000u&&((unsigned)rc&0xffffu)==EEXIST)return 0;
    return failed("Sony mkdir",rc);
}
#else
static int make_directory(const char *path){
    if(!mkdir(path,0700)||errno==EEXIST)return 0;
    return failed("mkdir",errno);
}
#endif
static int leaf(const char *name) {
    if(!name||!*name||strlen(name)>64||name[0]=='.')return 0;
    for(const char *p=name;*p;p++)if(!((*p>='a'&&*p<='z')||(*p>='0'&&*p<='9')||*p=='.'||*p=='-'))return 0;
    return 1;
}
#ifdef PS5_ABSOLUTE_STATE
static int reserved_path_valid(int dir){
    if(!reserved_context(dir))return failed("reserved context changed",EACCES);
    int fd=open(PRIVATE_STATE_BASE,O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);
    if(fd<0)return failed("reopen reserved directory",errno);
    struct stat s={0};int rc=fstat(fd,&s);close(fd);
    if(rc)return failed("recheck reserved directory",errno);
    if(s.st_uid!=0||!S_ISDIR(s.st_mode)||(s.st_mode&0077)||s.st_dev!=reserved_device||s.st_ino!=reserved_inode)
        return failed("reserved path changed",EACCES);
    return 0;
}
static int absolute_leaf(int dir,const char *name,char path[160],int temporary){
    if(reserved_path_valid(dir))return -1;
    if(!leaf(name))return failed("reserved filename",EINVAL);
    snprintf(path,160,temporary?PRIVATE_STATE_BASE"/.%s.new":PRIVATE_STATE_BASE"/%s",name);
    return 0;
}
#endif
static int private_object(int fd,int directory,size_t size,int context,int check_size) {
#ifndef PS5_RESERVED_STATE
    (void)context;
#endif
    struct stat s={0};
    if(fstat(fd,&s)){failed("fstat",errno);return 0;}
    errno=0;uid_t effective=geteuid();int effective_error=errno;
    errno=0;uid_t real=getuid();int real_error=errno;
    snprintf(identity_evidence,sizeof(identity_evidence),"UID:%s e%d EUID:%s e%d Owner:%s Mode:%04o Dir:%s",
        real==(uid_t)-1?"denied":real==0?"root":"ok",real_error,
        effective==(uid_t)-1?"denied":effective==0?"root":"ok",effective_error,
        s.st_uid==0?"root":s.st_uid==effective?"self":s.st_uid==real?"real":"other",
        (unsigned)(s.st_mode&07777),S_ISDIR(s.st_mode)?"yes":"no");
    if(effective==(uid_t)-1){failed("effective UID query",effective_error?effective_error:EACCES);return 0;}
    int owned=s.st_uid==effective;
#ifdef PS5_RESERVED_STATE
    if(context==reserved_fd){
        if(!reserved_context(context)){failed("reserved directory changed",EACCES);return 0;}
        owned=s.st_uid==0&&s.st_dev==reserved_device;
    }
#endif
    if(!owned){failed("owner check",EACCES);return 0;}
    if(s.st_mode&0077){failed("mode check",EACCES);return 0;}
    if(directory){if(!S_ISDIR(s.st_mode)){failed("directory type",EINVAL);return 0;}}
    else {
        size_t used=strlen(identity_evidence);
        snprintf(identity_evidence+used,sizeof(identity_evidence)-used," Reg:%s Links:%u Bytes:%lld/%zu",
            S_ISREG(s.st_mode)?"yes":"no",(unsigned)s.st_nlink,(long long)s.st_size,size);
        if(!S_ISREG(s.st_mode)){failed("file type",EINVAL);return 0;}
        int link_ok=s.st_nlink==1;
#ifdef PS5_ZERO_LINK_STATE
        /* Observed native title-local and root-worker metadata reports count 0.
         * Only the exact pinned private context qualifies. Counts >1 reject;
         * zero provides no hard-link detection guarantee. */
        if(s.st_nlink==0&&context==reserved_fd&&reserved_context(context)&&
            s.st_uid==0&&s.st_dev==reserved_device)link_ok=1;
#endif
        if(!link_ok){failed("link count",EINVAL);return 0;}
        if(check_size&&(s.st_size<0||(size_t)s.st_size!=size)){failed("file size",EINVAL);return 0;}
    }
    return 1;
}
int state_open(const char *directory) {
    failure_operation="none";failure_code=0;
    identity_evidence[0]=0;
#ifdef PS5_WORKER_STATE
    if(!directory||strcmp(directory,PRIVATE_STATE_BASE))return failed("worker private path",EACCES);
#endif
#ifdef PS5_RESERVED_STATE
    reserved_fd=-1;
    if(!strcmp(directory,PRIVATE_STATE_BASE)){
#ifdef PS5_WORKER_STATE
        if(geteuid()!=0)return failed("worker requires loader-provided root",EACCES);
#endif
        state_progress(13);
        int parent=open(PRIVATE_STATE_PARENT,O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);
        if(parent<0)return failed("open reserved parent",errno);
        struct stat p={0};
        state_progress(14);
        if(fstat(parent,&p)){int rc=failed("stat reserved parent",errno);close(parent);return rc;}
        if(!S_ISDIR(p.st_mode)||p.st_uid!=0){close(parent);return failed("reserved parent owner/type",EACCES);}
        state_progress(15);if(make_directory(directory)){close(parent);return -1;}
#ifdef PS5_ABSOLUTE_STATE
        state_progress(16);int fd=open(directory,O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);
#else
        int fd=openat(parent,"trophy-sync-live",O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);
#endif
        close(parent);
        if(fd<0)return failed("open reserved directory",errno);
        struct stat s={0};
        if(fstat(fd,&s)){int rc=failed("stat reserved directory",errno);close(fd);return rc;}
        if(s.st_dev!=p.st_dev){close(fd);return failed("reserved filesystem check",EACCES);}
        state_progress(17);reserved_fd=fd;reserved_device=s.st_dev;reserved_inode=s.st_ino;
        if(!private_object(fd,1,0,fd,1)){reserved_fd=-1;close(fd);return -1;}
        return fd;
    }
#endif
    if(make_directory(directory))return -1;
    int fd=open(directory,O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);
    if(fd<0)return failed("open directory",errno);
    if(fd>=0&&!private_object(fd,1,0,fd,1)){close(fd);fd=-1;}
    return fd;
}
int state_read(int dir,const char *name,void *bytes,size_t size) {
    failure_operation="none";failure_code=0;
    if(!leaf(name)||!bytes||!size||size>PRIVATE_STATE_LIMIT)return failed("read arguments",EINVAL);
    state_progress(18);
#ifdef PS5_ABSOLUTE_STATE
    char path[160];if(absolute_leaf(dir,name,path,0))return -1;
    int fd=open(path,O_RDONLY|O_NOFOLLOW|O_CLOEXEC|O_NONBLOCK);
#else
    int fd=openat(dir,name,O_RDONLY|O_NOFOLLOW|O_CLOEXEC|O_NONBLOCK);
#endif
    if(fd<0)return errno==ENOENT?1:failed("open private file",errno);
    int rc=-1;
    if(private_object(fd,0,size,dir,1)){
        size_t used=0;
        while(used<size){ssize_t n=read(fd,(char*)bytes+used,size-used);if(n<0&&errno==EINTR)continue;if(n<=0)break;used+=(size_t)n;}
        if(used!=size)failed("read private file",EIO);
        else if(private_object(fd,0,size,dir,1))rc=0;
    }
    close(fd);return rc;
}
int state_write(int dir,const char *name,const void *bytes,size_t size) {
    failure_operation="none";failure_code=0;
    if(!leaf(name)||!bytes||!size||size>PRIVATE_STATE_LIMIT)return failed("write arguments",EINVAL);
    char temporary[80];snprintf(temporary,sizeof(temporary),".%s.new",name);
    state_progress(19);
#ifdef PS5_ABSOLUTE_STATE
    char path[160],destination[160];
    if(absolute_leaf(dir,name,path,1)||absolute_leaf(dir,name,destination,0))return -1;
    int fd=open(path,O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC,0600);
#else
    int fd=openat(dir,temporary,O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC,0600);
#endif
    if(fd<0)return failed("create private file",errno);
    size_t used=0;int rc=-1;
    while(used<size){ssize_t n=write(fd,(const char*)bytes+used,size-used);if(n<0&&errno==EINTR)continue;if(n<=0)break;used+=(size_t)n;}
    if(used!=size)failed("write private file",errno);
    else if((state_progress(20),private_object(fd,0,size,dir,0))){
        state_progress(21);
        if(fsync(fd))failed("sync private file",errno);
        else if(!private_object(fd,0,size,dir,1)){}
#ifdef PS5_ABSOLUTE_STATE
        else if(reserved_path_valid(dir)){}
        else if((state_progress(22),rename(path,destination)))failed("publish private file",errno);
#else
        else if(renameat(dir,temporary,dir,name))failed("publish private file",errno);
#endif
        else if((state_progress(23),fsync(dir)))failed("sync private directory",errno);
        else rc=0;
    }
    close(fd);
    if(rc){
#ifdef PS5_ABSOLUTE_STATE
        if(!reserved_path_valid(dir))unlink(path);
#else
        unlinkat(dir,temporary,0);
#endif
    }
    return rc;
}
