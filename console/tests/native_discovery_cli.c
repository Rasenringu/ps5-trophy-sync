/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "../sync/native_discovery_ftp.h"
#include <stdio.h>
int main(void){char names[128][13];unsigned count=0;int rc=native_discover(9,names,&count);printf("%d %u\n",rc,count);for(unsigned i=0;i<count;i++)puts(names[i]);return 0;}
