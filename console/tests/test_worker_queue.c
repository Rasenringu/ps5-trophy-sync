/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Isolated MOCK files only. Reuse private-state attack fixtures. */
#define main reserved_state_tests
#include "test_reserved_state.c"
#undef main
#include "../sync/queue.h"
int main(void){
    reserved_state_tests();strcpy(parent,"/tmp/MOCK-reserved-XXXXXX");
    assert(mkdtemp(parent));snprintf(child,sizeof(child),"%s/trophy-sync-live",parent);
    int dir=state_open(TEST_DIRECTORY);assert(dir>=0);
    const char *installation="00000000-0000-4000-8000-000000000001";
    const char *profile="00000000-0000-4000-8000-000000000002";
    const char *origin="https://MOCK.example.test";
    const char *json="{\"mock\":true,\"batch_id\":\"MOCK_SAME_UUID_ON_RETRY\"}";
    SyncQueueItem item;unsigned slot=999;
    assert(sync_queue_load(dir,9,0,installation,profile,origin,&item)==1);
    assert(!sync_queue_put(dir,9,installation,profile,origin,json,&slot)&&slot==0);
    close(dir);dir=state_open(TEST_DIRECTORY);assert(dir>=0);
    assert(!sync_queue_load(dir,9,0,installation,profile,origin,&item));
    assert(!strcmp(item.json,json)&&!item.acknowledged);
    assert(sync_queue_load(dir,9,0,profile,installation,origin,&item)==-1);
    assert(sync_queue_load(dir,9,0,installation,profile,"https://OTHER.test",&item)==-1);
    for(unsigned n=1;n<SYNC_QUEUE_SLOTS;n++)assert(!sync_queue_put(dir,9,installation,profile,origin,json,&slot)&&slot==n);
    assert(sync_queue_put(dir,9,installation,profile,origin,json,&slot)==-2);
    assert(!sync_queue_load(dir,9,0,installation,profile,origin,&item));
    assert(!sync_queue_ack(dir,0,&item));
    assert(!sync_queue_put(dir,9,installation,profile,origin,json,&slot)&&slot==0);
    assert(!sync_queue_load(dir,9,0,installation,profile,origin,&item));
    item.json[2]='X';assert(!state_write(dir,"queue-00000009-00.bin",&item,sizeof(item)));
    assert(sync_queue_load(dir,9,0,installation,profile,origin,&item)==-1);
    assert(sync_queue_put(dir,9,installation,profile,origin,json,&slot)==-1);
    for(unsigned n=0;n<SYNC_QUEUE_SLOTS;n++){
        char name[64];snprintf(name,sizeof(name),"queue-00000009-%02u.bin",n);assert(!unlinkat(dir,name,0));
    }
    close(dir);assert(!rmdir(child));assert(!rmdir(parent));
    puts("PASS MOCK queue: restart reload preserves exact batch, scope/corruption fail closed, full queue retains pending, durable ack permits reuse.");
}
