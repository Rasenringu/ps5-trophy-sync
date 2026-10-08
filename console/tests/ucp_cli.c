/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "../readers/ucp.h"
#include <stdio.h>
#include <stdlib.h>
int main(int argc,char **argv) {
    if(argc!=2) return 2;
    FILE *f=fopen(argv[1],"rb");if(!f) return 2;
    if(fseek(f,0,SEEK_END)) { fclose(f);return 2; }
    long length=ftell(f);
    if(length<0 || length>64*1024*1024) { fclose(f);return 2; }
    rewind(f);unsigned char *bytes=malloc((size_t)length ? (size_t)length : 1);
    if(!bytes) { fclose(f);return 2; }
    if(fread(bytes,1,(size_t)length,f)!=(size_t)length) { free(bytes);fclose(f);return 2; }
    fclose(f);Ucp archive;int rc=ucp_validate(bytes,(size_t)length,&archive);
    UcpEntry entry;int definitions=rc==0 && ucp_find(&archive,"tropconf.json",&entry)==0;
    printf("%d %u %d\n",rc,rc==0 ? archive.count : 0,definitions);
    free(bytes);return 0;
}
