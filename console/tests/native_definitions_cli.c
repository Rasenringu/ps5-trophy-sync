/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "../readers/native_definitions.h"
#include <stdio.h>
#include <stdlib.h>
int main(int argc,char **argv) {
    if(argc!=2) return 2;
    FILE *f=fopen(argv[1],"rb");if(!f) return 2;
    if(fseek(f,0,SEEK_END)) { fclose(f);return 2; }
    long length=ftell(f);
    if(length<0 || length>64*1024*1024) { fclose(f);return 2; }
    rewind(f);unsigned char *b=malloc((size_t)length ? (size_t)length : 1);
    if(!b) { fclose(f);return 2; }
    if(fread(b,1,(size_t)length,f)!=(size_t)length) { free(b);fclose(f);return 2; }
    fclose(f);Ucp archive;NativeDefinitions definitions={0};
    int rc=ucp_validate(b,(size_t)length,&archive);
    if(!rc) rc=native_definitions(&archive,&definitions);
    unsigned bronze=0,silver=0,gold=0,platinum=0;
    for(unsigned i=0;i<definitions.count;i++) {
        switch(definitions.trophies[i].grade) { case 'B':bronze++;break;case 'S':silver++;break;case 'G':gold++;break;case 'P':platinum++;break; }
    }
    printf("%d %u %u %u %u %u\n",rc,definitions.count,bronze,silver,gold,platinum);
    native_definitions_free(&definitions);free(b);return 0;
}
