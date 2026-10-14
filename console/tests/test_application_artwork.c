/* SPDX-License-Identifier: GPL-3.0-or-later */
/* MOCK header-only image files: source selection/stability tests, not PNG
 * decoding or console validation. The API separately validates full PNG CRCs. */
#define _GNU_SOURCE 1
#define NATIVE_APPLICATION_ARTWORK_TEST 1
#include <assert.h>
#include "../sync/native_collect_assets.c"
static unsigned current=9,visits,stop;
int sceUserServiceGetForegroundUser(uint32_t *profile){*profile=current;return 0;}
static int visit(const unsigned char *bytes,size_t size,const char *title,void *unused){
    (void)unused;assert(size==100&&!memcmp(bytes,"\x89PNG\r\n\x1a\n",8));
    assert(!strcmp(title,"CUSA03804")||!strcmp(title,"PPSA74207"));visits++;return stop?-1:0;
}
int main(void){
    char root[]="/tmp/MOCK-native-app-art-XXXXXX";assert(mkdtemp(root));assert(!setenv("MOCK_APP_META_ROOT",root,1));
    const char *titles[]={"CUSA03804","PPSA74207","CUSA02344","PPSA01924"};
    unsigned char bytes[100]={0};memcpy(bytes,"\x89PNG\r\n\x1a\n",8);
    char path[512],target[512];
    for(unsigned i=0;i<4;i++){
        snprintf(path,sizeof(path),"%s/%s",root,titles[i]);assert(!mkdir(path,0700));
        snprintf(path,sizeof(path),"%s/%s/icon0.png",root,titles[i]);
        if(i==3){snprintf(target,sizeof(target),"%s/CUSA03804/icon0.png",root);assert(!symlink(target,path));continue;}
        int fd=open(path,O_WRONLY|O_CREAT|O_EXCL,0600);assert(fd>=0);
        if(i==2)bytes[0]=0;assert(write(fd,bytes,sizeof(bytes))==sizeof(bytes));close(fd);
    }
    sqlite3 *db=NULL;assert(!sqlite3_open(":memory:",&db));
    assert(!sqlite3_exec(db,"CREATE TABLE sessions(title_id TEXT);INSERT INTO sessions VALUES('CUSA03804'),('CUSA03804'),('PPSA74207'),('CUSA02344'),('PPSA01924'),('../../escape')",NULL,NULL,NULL));
    NativeApplicationArtworkCounts counts;assert(!native_collect_application_artwork(9,db,&counts,visit,NULL));
    assert(visits==2&&counts.found==2&&counts.missing==1&&counts.rejected==2);
    stop=1;assert(native_collect_application_artwork(9,db,&counts,visit,NULL)==-3);
    current=10;assert(native_collect_application_artwork(9,db,&counts,visit,NULL)==-2);
    sqlite3_close(db);
    for(unsigned i=0;i<4;i++){snprintf(path,sizeof(path),"%s/%s/icon0.png",root,titles[i]);assert(!unlink(path));snprintf(path,sizeof(path),"%s/%s",root,titles[i]);assert(!rmdir(path));}
    assert(!rmdir(root));puts("PASS MOCK application icons: actual session IDs, deduplication, bounded stable reads, invalid/path/symlink refusal, profile change, visitor failure.");return 0;
}
