/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Synthetic files only. Exercise the exact collector's two-pass chunk reader. */
#define _GNU_SOURCE 1
#include <assert.h>
#include "../sync/native_collect_assets.c"
int main(void){
    char path[]="/tmp/MOCK-native-package-XXXXXX";int fd=mkstemp(path);assert(fd>=0);
    const size_t length=71u*1024*1024;assert(!ftruncate(fd,(off_t)length));
    unsigned char marker=123;assert(pwrite(fd,&marker,1,65536)==1);assert(pwrite(fd,&marker,1,(off_t)length-1)==1);
    size_t size=0;int missing=0;unsigned char *bytes=stable_read(path,128u*1024*1024,&size,&missing);
    assert(bytes&&size==length&&!missing&&bytes[65536]==marker&&bytes[length-1]==marker);free(bytes);
    assert(!stable_read(path,64u*1024*1024,&size,&missing)&&!missing);
    struct stat before,after;assert(!fstat(fd,&before));
    char link[256];snprintf(link,sizeof(link),"%s-link",path);assert(!symlink(path,link));
    assert(!stable_read(link,128u*1024*1024,&size,&missing));
    assert(!fstat(fd,&after)&&same(&before,&after));
    close(fd);assert(!unlink(link));assert(!unlink(path));
    puts("PASS MOCK package stability: >64 MiB chunked second read, end/chunk boundary bytes, bounded rejection, symlink refusal, unchanged source.");return 0;
}
