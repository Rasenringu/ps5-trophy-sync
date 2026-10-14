/* SPDX-License-Identifier: GPL-3.0-or-later */
#define _POSIX_C_SOURCE 200809L
#include <assert.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>
static int watched=-1,writer=-1,reads,mutate;
static ssize_t tracked_pread(int fd,void *out,size_t n,off_t at){
    if(fd==watched&&++reads==4&&mutate){unsigned char changed=99;assert(pwrite(writer,&changed,1,1025)==1);}
    return pread(fd,out,n,at);
}
#define pread tracked_pread
#include "../readers/ps4_image_snapshot.c"
#undef pread
static void le(unsigned char *p,uint64_t n){for(unsigned i=0;i<8;i++)p[i]=(unsigned char)(n>>(8*i));}
int main(void){
    char folder[]="/tmp/ps4-snapshot-test-XXXXXX";assert(mkdtemp(folder));char src[256],dst[256];
    snprintf(src,sizeof(src),"%s/source",folder);snprintf(dst,sizeof(dst),"%s/copy",folder);
    writer=open(src,O_RDWR|O_CREAT|O_EXCL,0600);assert(writer>=0);
    unsigned char bytes[131072],saved[sizeof(bytes)];memset(bytes,42,sizeof(bytes));le(bytes,1);le(bytes+8,20130315);
    assert(write(writer,bytes,sizeof(bytes))==sizeof(bytes));memcpy(saved,bytes,sizeof(bytes));
    int source=open(src,O_RDONLY),destination=open(dst,O_RDWR|O_CREAT|O_EXCL,0600);assert(source>=0&&destination>=0);
    watched=source;reads=0;
    assert(!ps4_image_snapshot(source,destination,sizeof(bytes)));
    assert(pread(destination,bytes,sizeof(bytes),0)==sizeof(bytes)&&!memcmp(bytes,saved,sizeof(bytes)));
    assert(pread(source,bytes,sizeof(bytes),0)==sizeof(bytes)&&!memcmp(bytes,saved,sizeof(bytes)));
    assert(ps4_image_snapshot(source,destination,sizeof(bytes))<0); /* no overwrites */
    assert(!ftruncate(destination,0));assert(ps4_image_snapshot(writer,destination,sizeof(bytes))<0);
    assert(ps4_image_snapshot(source,destination,sizeof(bytes)-1)<0);
    assert(!fchmod(destination,0644));assert(ps4_image_snapshot(source,destination,sizeof(bytes))<0);assert(!fchmod(destination,0600));
    assert(pwrite(writer,"SQLite format 3",16,0)==16);assert(ps4_image_snapshot(source,destination,sizeof(bytes))<0);
    assert(pwrite(writer,saved,sizeof(saved),0)==sizeof(saved));reads=0;mutate=1;
    assert(ps4_image_snapshot(source,destination,sizeof(bytes))<0); /* source changed during verification */
    close(source);close(destination);close(writer);unlink(src);unlink(dst);rmdir(folder);
    puts("PASS private encrypted snapshot: source preservation, bounds, no overwrites, source changes, read-only descriptors");return 0;
}
