/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "../transport/https_json.h"
#include <stdio.h>
#include <stdlib.h>
int main(int argc,char **argv) {
    if(argc!=5&&argc!=6)return 2;
    char ca[8192],body[16384];FILE *f=fopen(argv[3],"rb");if(!f)return 2;
    size_t n=fread(ca,1,sizeof(ca)-1,f);fclose(f);ca[n]=0;
    JsonResponse r=https_json(argc==6?argv[5]:"127.0.0.1",(unsigned short)atoi(argv[1]),argv[2],ca,argv[4],NULL,"{}",body,sizeof(body));
    printf("%d %u %d %d %zu\n",r.tls.rc,r.tls.verify_flags,r.tls.verified_handshake,r.status,r.size);
}
