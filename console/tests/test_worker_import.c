/* SPDX-License-Identifier: GPL-3.0-or-later */
/* MOCK HTTPS; isolated private-state fixture. No console/service contacted. */
#define main reserved_state_tests
#include "test_reserved_state.c"
#undef main
#define main worker_entry_not_run
#include "../worker/main.c"
#undef main
static unsigned requests;
static int failure_mode;
static const char *batch="00000000-0000-4000-8000-000000000003";
static const char *payload="{\"mock\":true,\"batch_id\":\"00000000-0000-4000-8000-000000000003\"}";
int sceUserServiceInitialize(void *unused){(void)unused;return 0;}
int sceUserServiceGetForegroundUser(uint32_t *user){*user=selected;return 0;}
uint64_t sceKernelGetProcessTime(void){return 1000000;}
int sceKernelUsleep(uint32_t time){(void)time;return 0;}
int pair_start(PairClient *c,UiModel *m,unsigned p,unsigned long long now){(void)c;(void)m;(void)p;(void)now;return 0;}
void pair_tick(PairClient *c,UiModel *m,unsigned long long now){(void)c;(void)m;(void)now;}
int native_collect(unsigned profile,NativeCollected *counts,NativeCollectionVisitor visitor,void *context){(void)profile;(void)counts;(void)visitor;(void)context;return -1;}
JsonResponse https_json(const char *ip,unsigned short port,const char *name,const char *ca,const char *path,const char *token,const char *json,char *body,size_t capacity){
    assert(!strcmp(ip,PROBE_IP)&&port==PROBE_PORT&&!strcmp(name,PROBE_IP)&&!strcmp(ca,PROBE_CA));
    assert(!strcmp(path,"/api/device/sync")&&!strcmp(token,"MOCK_TEST_TOKEN")&&!strcmp(json,payload));
    requests++;JsonResponse r={.status=200,.tls={.rc=0}};
    if(failure_mode==1||(!failure_mode&&requests<3)){r.tls.rc=-123;return r;}
    if(failure_mode==2){r.status=401;return r;}
    snprintf(body,capacity,"{\"status\":\"duplicate\",\"batch_id\":\"%s\"}",failure_mode==3?"WRONG_BATCH":batch);return r;
}
int main(void){
    reserved_state_tests();strcpy(parent,"/tmp/MOCK-reserved-XXXXXX");assert(mkdtemp(parent));snprintf(child,sizeof(child),"%s/trophy-sync-live",parent);
    int directory=state_open(TEST_DIRECTORY);assert(directory>=0);selected=9;assert(!pthread_mutex_init(&lock,NULL));
    PairClient client={.directory=directory,.profile=9};
    snprintf(client.installation_id,sizeof(client.installation_id),"00000000-0000-4000-8000-000000000001");
    snprintf(client.profile_uuid,sizeof(client.profile_uuid),"00000000-0000-4000-8000-000000000002");
    snprintf(client.origin,sizeof(client.origin),"https://MOCK.example.test");snprintf(client.device_token,sizeof(client.device_token),"MOCK_TEST_TOKEN");
    char reply[200];snprintf(reply,sizeof(reply),"{\"status\":\"imported\",\"batch_id\":\"%s\"}",batch);assert(acknowledged(payload,reply));
    assert(!acknowledged(payload,"{\"status\":\"imported\",\"status\":\"duplicate\",\"batch_id\":\"00000000-0000-4000-8000-000000000003\"}"));
    assert(!acknowledged(payload,"{\"status\":\"imported\",\"batch_id\":\"OTHER\"}"));
    for(failure_mode=0;failure_mode<4;failure_mode++){
        requests=0;unsigned slot;SyncQueueItem item;UiModel model={.phase=UI_CONNECTED};
        assert(!sync_queue_put(directory,9,client.installation_id,client.profile_uuid,client.origin,payload,&slot)&&slot==0);
        int rc=flush_queue(&client,&model);assert(failure_mode?rc==-1:rc==0);
        assert(requests==(failure_mode==0?3:failure_mode==1?5:1));
        assert(!sync_queue_load(directory,9,0,client.installation_id,client.profile_uuid,client.origin,&item));
        assert(item.acknowledged==(unsigned)(failure_mode==0)&&!strcmp(item.json,payload));
        assert(!unlinkat(directory,"queue-00000009-00.bin",0));
    }
    close(directory);assert(!rmdir(child));assert(!rmdir(parent));
    puts("PASS MOCK import: same saved UUID/body on retries, exact duplicate ACK required, 5-attempt transport bound, revocation/invalid ACK retain pending data.");return 0;
}
