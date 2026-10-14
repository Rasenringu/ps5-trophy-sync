/* SPDX-License-Identifier: GPL-3.0-or-later */
#define _POSIX_C_SOURCE 200809L
#include "ps4_image_snapshot.h"
#include <stdint.h>
#include <string.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <unistd.h>
static uint64_t le64(const unsigned char *p){uint64_t n=0;for(unsigned i=0;i<8;i++)n|=(uint64_t)p[i]<<(8*i);return n;}
static int equal(const struct stat *a,const struct stat *b){return a->st_dev==b->st_dev&&a->st_ino==b->st_ino&&a->st_size==b->st_size&&a->st_mtime==b->st_mtime&&a->st_ctime==b->st_ctime;}
static int take(int fd,unsigned char *out,size_t n,off_t at){size_t used=0;while(used<n){ssize_t k=pread(fd,out+used,n-used,at+(off_t)used);if(k<=0)return -1;used+=(size_t)k;}return 0;}
int ps4_image_snapshot(int source,int destination,size_t limit){
    struct stat before,after,dest;unsigned char a[65536],b[65536];int rc=-1;
    if(fstat(source,&before)||fstat(destination,&dest)||!S_ISREG(before.st_mode)||!S_ISREG(dest.st_mode)||
       before.st_size<1024||(uint64_t)before.st_size>limit||dest.st_size||
       (fcntl(source,F_GETFL)&O_ACCMODE)!=O_RDONLY||(fcntl(destination,F_GETFL)&O_ACCMODE)!=O_RDWR||
       dest.st_uid!=geteuid()||dest.st_nlink!=1||(dest.st_mode&077)!=0||
       (before.st_dev==dest.st_dev&&before.st_ino==dest.st_ino))return -1;
    struct flock guard={.l_type=F_RDLCK,.l_whence=SEEK_SET,.l_start=0,.l_len=0};
    if(fcntl(source,F_SETLK,&guard))return -2;
    if(take(source,a,1024,0)||le64(a)!=1||le64(a+8)!=20130315)goto done;
    for(off_t at=0;at<before.st_size;){
        size_t n=(size_t)(before.st_size-at);if(n>sizeof(a))n=sizeof(a);
        if(take(source,a,n,at))goto done;
        size_t used=0;while(used<n){ssize_t k=pwrite(destination,a+used,n-used,at+(off_t)used);if(k<=0)goto done;used+=(size_t)k;}
        at+=(off_t)n;
    }
    if(fstat(source,&after)||!equal(&before,&after)||fsync(destination))goto done;
    for(off_t at=0;at<before.st_size;){
        size_t n=(size_t)(before.st_size-at);if(n>sizeof(a))n=sizeof(a);
        if(take(source,a,n,at)||take(destination,b,n,at)||memcmp(a,b,n))goto done;
        at+=(off_t)n;
    }
    if(fstat(source,&after)||!equal(&before,&after))goto done;
    rc=0;
done:memset(a,0,sizeof(a));memset(b,0,sizeof(b));guard.l_type=F_UNLCK;fcntl(source,F_SETLK,&guard);return rc;
}
