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
static int application_mode;
static unsigned application_uploads;
static int ps4_mode;
static unsigned ps4_uploads;
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
    if(!strcmp(path,"/api/device/ps4-artwork/check")){
        assert(ps4_mode&&strstr(json,"NPWR00001_00"));
        snprintf(body,capacity,"%s",ps4_mode==1?"{\"needed\":false}":ps4_mode==3?"{\"needed\":true,\"needed\":false}":"{\"needed\":true}");
        return (JsonResponse){.status=200,.tls={.verified_handshake=1}};
    }
    if(!strcmp(path,"/api/device/application-artwork/check")){
        assert(!strcmp(token,"MOCK_TEST_TOKEN")&&strstr(json,"CUSA03804"));
        snprintf(body,capacity,"%s",application_mode==1?"{\"needed\":false}":application_mode==3?"{\"needed\":true,\"needed\":false}":"{\"needed\":true}");
        return (JsonResponse){.status=200,.tls={.verified_handshake=1}};
    }
    assert(!strcmp(path,"/api/device/sync")&&!strcmp(token,"MOCK_TEST_TOKEN"));
    if(ps4_mode){
        assert(strstr(json,"\"schema_version\":4")&&strstr(json,"\"source\":\"ps4_bc\"")&&strstr(json,"NPWR00001_00"));
        sqlite3 *db=NULL;sqlite3_stmt *q=NULL;assert(!sqlite3_open(":memory:",&db));
        assert(!sqlite3_prepare_v2(db,"SELECT json_extract(?1,'$.batch_id')",-1,&q,NULL));sqlite3_bind_text(q,1,json,-1,SQLITE_STATIC);assert(sqlite3_step(q)==SQLITE_ROW);
        snprintf(body,capacity,"{\"status\":\"imported\",\"batch_id\":\"%s\"}",sqlite3_column_text(q,0));sqlite3_finalize(q);sqlite3_close(db);
        return (JsonResponse){.status=200,.tls={.verified_handshake=1}};
    }
    assert(!strcmp(json,payload));
    requests++;JsonResponse r={.status=200,.tls={.rc=0,.verified_handshake=1}};
    if(failure_mode==1||(!failure_mode&&requests<3)){r.tls.rc=-123;return r;}
    if(failure_mode==2){r.status=401;return r;}
    if(failure_mode>=4){
        r.status=failure_mode==7?429:422;r.tls.rc=-1;
        if(failure_mode==5)r.tls.verified_handshake=0;
        if(failure_mode==6)r.tls.verify_flags=1;
        return r;
    }
    snprintf(body,capacity,"{\"status\":\"duplicate\",\"batch_id\":\"%s\"}",failure_mode==3?"WRONG_BATCH":batch);return r;
}
JsonResponse https_binary(const char *ip,unsigned short port,const char *name,const char *ca,const char *path,const char *token,const unsigned char *payload,size_t size,char *body,size_t capacity){
    assert(!strcmp(ip,PROBE_IP)&&port==PROBE_PORT&&!strcmp(name,PROBE_IP)&&!strcmp(ca,PROBE_CA));
    assert(!strcmp(token,"MOCK_TEST_TOKEN")&&size==100);
    if(ps4_mode){assert(!strcmp(path,"/api/device/ps4-artwork/NPWR00001_00"));ps4_uploads++;}
    else{assert(!strcmp(path,"/api/device/application-artwork/CUSA03804"));application_uploads++;}
    unsigned char hash[32];char sha[65];assert(!mbedtls_sha256(payload,size,hash,0));
    for(unsigned i=0;i<32;i++)snprintf(sha+i*2,3,"%02x",hash[i]);
    snprintf(body,capacity,"{\"status\":\"stored\",\"title_id\":\"%s\",\"sha256\":\"%s\"}",ps4_mode?(ps4_mode==4?"NPWR00002_00":"NPWR00001_00"):(application_mode==4?"PPSA12345":"CUSA03804"),sha);
    return (JsonResponse){.status=200,.tls={.verified_handshake=1}};
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
    for(failure_mode=0;failure_mode<8;failure_mode++){
        requests=0;unsigned slot;SyncQueueItem item;UiModel model={.phase=UI_CONNECTED};
        assert(!sync_queue_put(directory,9,client.installation_id,client.profile_uuid,client.origin,payload,&slot)&&slot==0);
        int rc=flush_queue(&client,&model);assert(failure_mode?rc==-1:rc==0);
        assert(requests==(failure_mode==0?3:failure_mode==1||failure_mode>=5?5:1));
        if(failure_mode==4){
            assert(strstr(model.error,"Import rejected by server (422)"));
            assert(strstr(model.reader_status,"Update the serving API"));
        }
        assert(!sync_queue_load(directory,9,0,client.installation_id,client.profile_uuid,client.origin,&item));
        assert(item.acknowledged==(unsigned)(failure_mode==0)&&!strcmp(item.json,payload));
        assert(!unlinkat(directory,"queue-00000009-00.bin",0));
    }
    mbedtls_entropy_context entropy;mbedtls_ctr_drbg_context rng;
    mbedtls_entropy_init(&entropy);mbedtls_ctr_drbg_init(&rng);
    assert(!mbedtls_ctr_drbg_seed(&rng,mbedtls_entropy_func,&entropy,(const unsigned char*)"MOCK",4));
    Ps4StateRecord ps4row={.id=0,.grade=4,.unlocked=0};
    Ps4State ps4state={.title="NPWR00001_00",.count=1,.records=&ps4row};unsigned char ps4package[100]={0};
    for(ps4_mode=1;ps4_mode<=4;ps4_mode++){
        UiModel model={.phase=UI_CONNECTED};QueueContext context={&client,&model,&rng,0};ps4_uploads=0;
        int rc=queue_ps4(&ps4state,ps4package,sizeof(ps4package),&context);
        assert(rc==((ps4_mode==3||ps4_mode==4)?-1:0)&&context.queued==1);
        assert(ps4_uploads==(unsigned)(ps4_mode==2||ps4_mode==4));
        SyncQueueItem item;assert(!sync_queue_load(directory,9,0,client.installation_id,client.profile_uuid,client.origin,&item)&&item.acknowledged);
        assert(!unlinkat(directory,"queue-00000009-00.bin",0));
    }
    ps4_mode=0;mbedtls_ctr_drbg_free(&rng);mbedtls_entropy_free(&entropy);
    close(directory);assert(!rmdir(child));assert(!rmdir(parent));
    UiModel error_model={.phase=UI_CONNECTED};
    JsonResponse error_response={.status=413,.tls={.verified_handshake=1}};
    assert(fail_response(&error_model,"Artwork upload",&error_response)==-1);
    assert(strstr(error_model.error,"Artwork upload HTTP (413)"));
    char saved_error[sizeof(error_model.error)];memcpy(saved_error,error_model.error,sizeof(saved_error));
    fail_collection(&error_model,-3);assert(!memcmp(saved_error,error_model.error,sizeof(saved_error)));
    error_model.phase=UI_CONNECTED;error_response.tls.rc=-123;error_response.tls.connect_stage=7;error_response.tls.posix_errno=60;
    assert(fail_response(&error_model,"Artwork check",&error_response)==-1);
    assert(strstr(error_model.error,"Artwork check HTTPS: stage 7 errno 60"));
    fail_collection(&error_model,-3);assert(strstr(error_model.error,"Artwork check HTTPS"));
    error_model.phase=UI_CONNECTED;
    error_response.tls=(HttpsResult){.rc=MBEDTLS_ERR_SSL_TIMEOUT,.verified_handshake=1,
        .connect_stage=12,.phase=HTTPS_PHASE_RESPONSE_HEADERS,
        .bytes_sent=70u*1024*1024,.payload_size=70u*1024*1024};
    assert(fail_response(&error_model,"Artwork upload",&error_response)==-1);
    assert(strstr(error_model.error,"Artwork upload timeout waiting for reply; 70/70 MiB sent"));
    fail_collection(&error_model,-3);assert(strstr(error_model.error,"timeout waiting for reply"));
    unsigned char application_image[100]={0};memcpy(application_image,"\x89PNG\r\n\x1a\n",8);
    for(application_mode=1;application_mode<=4;application_mode++){
        UiModel application_model={.phase=UI_CONNECTED};QueueContext context={&client,&application_model,NULL,0};application_uploads=0;
        int rc=queue_application_artwork(application_image,sizeof(application_image),"CUSA03804",&context);
        assert(rc==((application_mode==3||application_mode==4)?-1:0));
        assert(application_uploads==(unsigned)(application_mode==2||application_mode==4));
    }
    puts("PASS MOCK import: same saved UUID/body on retries, exact duplicate ACK required, 5-attempt transport bound, revocation/invalid ACK retain pending data.");return 0;
}
