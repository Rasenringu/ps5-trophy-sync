/* Synthetic local CLI; not a console result. */
#include "../readers/native_activity.h"
#include <stdint.h>
#include <stdio.h>
int sceUserServiceGetForegroundUser(uint32_t *user){*user=0x12345678;return 0;}
int main(int argc,char **argv){
 if(argc!=2)return 2;sqlite3 *db=NULL;NativeActivityCounts counts;
 int rc=native_activity_collect(argv[1],0x12345678,&db,&counts);
 fprintf(stderr,"rc=%d rows=%u sessions=%u complete=%u incomplete=%u rejected=%u\n",rc,counts.rows,counts.sessions,counts.completed,counts.incomplete,counts.rejected);
 if(rc)return 1;
 for(unsigned first=0;first<counts.sessions;){unsigned count=counts.sessions-first;if(count>8)count=8;char body[8193];
  if(native_activity_batch(db,"00000000-0000-4000-8000-000000000001",first,count,body)){sqlite3_close(db);return 3;}puts(body);first+=count;}
 sqlite3_close(db);return 0;
}
