/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Console-local read-only source worker. Direct validated HTTPS to service;
 * private credentials/queue, bounded loopback status. PS4 uses temporary own
 * process permissions for disposable copies, without changing other processes. */
#include "status.h"
#include "../pairing/client.h"
#include "../sync/native_collect_assets.h"
#include "../sync/native_export.h"
#include "../sync/ps4_collect.h"
#include "../sync/ps4_export.h"
#include "../readers/native_activity.h"
#include "../sync/queue.h"
#include "../transport/https_json.h"
#include "../transport/https_binary.h"
#include <mbedtls/sha256.h>
#include <mbedtls/ssl.h>
#include "probe_config.h"
#include <mbedtls/ctr_drbg.h>
#include <mbedtls/entropy.h>
#include <mbedtls/platform_util.h>
#include <netinet/in.h>
#include <pthread.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/select.h>
#include <sys/socket.h>
#include <unistd.h>
int __patch_init(void){return 0;}
extern int sceUserServiceInitialize(void*);
extern int sceUserServiceGetForegroundUser(uint32_t*);
extern uint64_t sceKernelGetProcessTime(void);
extern int sceKernelUsleep(uint32_t);
static pthread_mutex_t lock;
static UiModel published;
static atomic_int stopping;
static unsigned selected;
static uint64_t now_ms(void){return sceKernelGetProcessTime()/1000;}
static int same_user(void){uint32_t user=UINT32_MAX;return !atomic_load(&stopping)&&!sceUserServiceGetForegroundUser(&user)&&user==selected;}
static void publish(UiModel *model){pthread_mutex_lock(&lock);published=*model;pthread_mutex_unlock(&lock);}
static int fail(UiModel *model,const char *action,int rc){
    model->phase=UI_ERROR;model->manual_code[0]=0;
    snprintf(model->error,sizeof(model->error),"%s (%d). Close App; pending batches retained.",action,rc);
    snprintf(model->sync_status,sizeof(model->sync_status),"Sync failed: %s",action);publish(model);return -1;
}
static int fail_response(UiModel *model,const char *action,const JsonResponse *response){
    char detail[100];
    if(response->tls.rc||!response->tls.verified_handshake||response->tls.verify_flags){
        if(response->tls.phase){
            snprintf(model->reader_status,sizeof(model->reader_status),"HTTPS phase %u: HTTP %d; TCP stage %d errno %d; verify %x; sent %llu/%llu bytes",
                response->tls.phase,response->status,response->tls.connect_stage,response->tls.posix_errno,
                response->tls.verify_flags,(unsigned long long)response->tls.bytes_sent,
                (unsigned long long)response->tls.payload_size);
            const char *phase=response->tls.phase==HTTPS_PHASE_UPLOAD?"sending body":
                response->tls.phase==HTTPS_PHASE_RESPONSE_HEADERS?"waiting for reply":
                response->tls.phase==HTTPS_PHASE_RESPONSE_BODY?"reading reply":
                response->tls.phase==HTTPS_PHASE_HANDSHAKE?"TLS handshake":"request headers";
            snprintf(detail,sizeof(detail),"%s %s %s; %llu/%llu MiB sent",action,
                response->tls.rc==MBEDTLS_ERR_SSL_TIMEOUT?"timeout":"HTTPS error",phase,
                (unsigned long long)(response->tls.bytes_sent/(1024*1024)),
                (unsigned long long)(response->tls.payload_size/(1024*1024)));
            return fail(model,detail,response->tls.rc?response->tls.rc:-1);
        }
        snprintf(detail,sizeof(detail),"%s HTTPS: stage %d errno %d verify %x",action,
                 response->tls.connect_stage,response->tls.posix_errno,response->tls.verify_flags);
        return fail(model,detail,response->tls.rc?response->tls.rc:-1);
    }
    snprintf(detail,sizeof(detail),"%s HTTP",action);return fail(model,detail,response->status);
}
static void fail_collection(UiModel *model,int rc){
    /* A visitor may already have published a precise queue/HTTP/TLS error. */
    if(model->phase!=UI_ERROR)
        fail(model,rc==-2?"Profile changed during read":rc<=-100?"Enable FTP2121 v0.21.1 for trophy discovery":"Native trophy collection failed",rc);
}
static int acknowledged(const char *input,const char *reply){
    sqlite3 *db=NULL;sqlite3_stmt *statement=NULL;int ok=0;
    if(sqlite3_open(":memory:",&db))goto done;
    sqlite3_limit(db,SQLITE_LIMIT_LENGTH,16384);
    const char *sql="SELECT json_valid(?1) AND json_valid(?2) AND json_extract(?1,'$.batch_id')=json_extract(?2,'$.batch_id') AND json_extract(?2,'$.status') IN ('imported','duplicate') AND NOT EXISTS(SELECT 1 FROM json_tree(?2) GROUP BY fullkey HAVING count(*)>1)";
    if(sqlite3_prepare_v2(db,sql,-1,&statement,NULL))goto done;
    sqlite3_bind_text(statement,1,input,-1,SQLITE_STATIC);sqlite3_bind_text(statement,2,reply,-1,SQLITE_STATIC);
    ok=sqlite3_step(statement)==SQLITE_ROW&&sqlite3_column_int(statement,0)==1;
done:sqlite3_finalize(statement);sqlite3_close(db);return ok;
}
static int flush_queue(PairClient *client,UiModel *model){
    SyncQueueItem item;char reply[16384];
    for(unsigned slot=0;slot<SYNC_QUEUE_SLOTS;slot++){
        if(!same_user())return fail(model,"Profile changed",-2);
        int rc=sync_queue_load(client->directory,selected,slot,client->installation_id,client->profile_uuid,client->origin,&item);
        if(rc==1)continue;
        if(rc<0)return fail(model,"Queue integrity or ownership",rc);
        if(item.acknowledged)continue;
        int success=0;
        for(unsigned attempt=0;attempt<5&&same_user();attempt++){
            snprintf(model->sync_status,sizeof(model->sync_status),"Sync: sending saved batch %u (attempt %u/5)",slot+1,attempt+1);publish(model);
            JsonResponse response=https_json(PROBE_IP,PROBE_PORT,PROBE_IP,PROBE_CA,"/api/device/sync",client->device_token,item.json,reply,sizeof(reply));
            if(!response.tls.rc&&response.status==200&&acknowledged(item.json,reply)){success=1;break;}
            if(!response.tls.rc&&response.status==200)return fail(model,"Import acknowledgement invalid",200);
            if(!response.tls.rc&&response.status>=400&&response.status<500&&response.status!=429)return fail(model,response.status==401?"Device credential revoked":"Import rejected",response.status);
            if(attempt==4)return fail(model,"HTTPS import unavailable; queued",response.tls.rc?response.tls.rc:response.status);
            unsigned seconds=1u<<attempt;for(unsigned n=0;n<seconds*10&&same_user();n++)sceKernelUsleep(100000);
        }
        if(!success)return fail(model,"Profile changed; queued",-2);
        if(sync_queue_ack(client->directory,slot,&item))return fail(model,"Save import acknowledgement",-1);
        mbedtls_platform_zeroize(reply,sizeof(reply));
    }
    mbedtls_platform_zeroize(&item,sizeof(item));return 0;
}
typedef struct {PairClient *client;UiModel *model;mbedtls_ctr_drbg_context *rng;unsigned queued;} QueueContext;
static int queue_rows(sqlite3 *db,unsigned records,int (*batch)(sqlite3*,const char*,unsigned,unsigned,char*),void *opaque){
    QueueContext *context=opaque;
    for(unsigned first=0;first<records;){
        if(!same_user())return -1;
        unsigned char random[16];if(mbedtls_ctr_drbg_random(context->rng,random,sizeof(random)))return -1;
        random[6]=(random[6]&15)|64;random[8]=(random[8]&63)|128;
        char uuid[37];snprintf(uuid,sizeof(uuid),"%02x%02x%02x%02x-%02x%02x-%02x%02x-%02x%02x-%02x%02x%02x%02x%02x%02x",random[0],random[1],random[2],random[3],random[4],random[5],random[6],random[7],random[8],random[9],random[10],random[11],random[12],random[13],random[14],random[15]);
        unsigned count=records-first;if(count>8)count=8;char json[8193];
        while(count&&batch(db,uuid,first,count,json))count--;
        if(!count)return -1;
        unsigned slot;
        if(sync_queue_put(context->client->directory,selected,context->client->installation_id,context->client->profile_uuid,context->client->origin,json,&slot))return -1;
        context->queued++;first+=count;
        snprintf(context->model->sync_status,sizeof(context->model->sync_status),"Sync: %u batches safely queued",context->queued);publish(context->model);
        if(first%256==0&&flush_queue(context->client,context->model))return -1;
    }
    return 0;
}
static int queue_collection(sqlite3 *db,unsigned records,void *opaque){return queue_rows(db,records,native_export_batch,opaque);}
static int queue_activity_collection(sqlite3 *db,unsigned records,void *opaque){
    QueueContext *context=opaque;
    for(unsigned first=0;first<records;){
        if(!same_user())return -1;
        unsigned char random[16];if(mbedtls_ctr_drbg_random(context->rng,random,sizeof(random)))return -1;
        random[6]=(random[6]&15)|64;random[8]=(random[8]&63)|128;
        char uuid[37];snprintf(uuid,sizeof(uuid),"%02x%02x%02x%02x-%02x%02x-%02x%02x-%02x%02x-%02x%02x%02x%02x%02x%02x",random[0],random[1],random[2],random[3],random[4],random[5],random[6],random[7],random[8],random[9],random[10],random[11],random[12],random[13],random[14],random[15]);
        unsigned count=records-first;if(count>8)count=8;char json[8193];
        while(count&&native_activity_batch(db,uuid,first,count,json))count--;
        if(!count)return -1;
        unsigned slot;
        if(sync_queue_put(context->client->directory,selected,context->client->installation_id,context->client->profile_uuid,context->client->origin,json,&slot))return -1;
        context->queued++;first+=count;
        snprintf(context->model->sync_status,sizeof(context->model->sync_status),"Sync: %u batches safely queued",context->queued);publish(context->model);
        if(first%256==0&&flush_queue(context->client,context->model))return -1;
    }
    return 0;
}
static int queue_assets(sqlite3 *memory,unsigned count,const unsigned char *package,size_t size,const char *title,void *opaque){
    QueueContext *context=opaque;
    if(queue_collection(memory,count,opaque))return fail(context->model,"Trophy queue failed",-1);
    if(flush_queue(context->client,context->model))return -1;
    if(!same_user())return fail(context->model,"Profile changed before artwork",-2);
    unsigned char hash[32];char digest[65],json[256],body[512];
    if(mbedtls_sha256(package,size,hash,0))return fail(context->model,"Artwork digest failed",-1);
    for(unsigned i=0;i<32;i++)snprintf(digest+i*2,3,"%02x",hash[i]);
    snprintf(json,sizeof(json),"{\"title_id\":\"%s\",\"sha256\":\"%s\"}",title,digest);
    JsonResponse response=https_json(PROBE_IP,PROBE_PORT,PROBE_IP,PROBE_CA,"/api/device/artwork/check",context->client->device_token,json,body,sizeof(body));
    if(response.tls.rc||!response.tls.verified_handshake||response.tls.verify_flags||response.status!=200)return fail_response(context->model,"Artwork check",&response);
    sqlite3_stmt *check=NULL;int needed=-1;
    if(!sqlite3_prepare_v2(memory,"SELECT json_extract(?1,'$.needed') WHERE json_valid(?1) AND json_type(?1,'$.needed') IN ('true','false')",-1,&check,NULL)){
        sqlite3_bind_text(check,1,body,-1,SQLITE_STATIC);if(sqlite3_step(check)==SQLITE_ROW)needed=sqlite3_column_int(check,0);
    }
    sqlite3_finalize(check);if(needed<0)return fail(context->model,"Artwork check response invalid",200);if(!needed)return 0;
    snprintf(context->model->error,sizeof(context->model->error),"Uploading game artwork and translations: %s",title);publish(context->model);
    response=https_binary(PROBE_IP,PROBE_PORT,PROBE_IP,PROBE_CA,"/api/device/artwork",context->client->device_token,package,size,body,sizeof(body));
    if(response.tls.rc||!response.tls.verified_handshake||response.tls.verify_flags||response.status!=200)return fail_response(context->model,"Artwork upload",&response);
    if(!same_user())return fail(context->model,"Profile changed after artwork",-2);
    check=NULL;int valid=0;
    if(!sqlite3_prepare_v2(memory,"SELECT json_extract(?1,'$.status')='stored' AND json_extract(?1,'$.title_id')=?2 AND json_extract(?1,'$.sha256')=?3 WHERE json_valid(?1)",-1,&check,NULL)){
        sqlite3_bind_text(check,1,body,-1,SQLITE_STATIC);sqlite3_bind_text(check,2,title,-1,SQLITE_STATIC);sqlite3_bind_text(check,3,digest,-1,SQLITE_STATIC);
        if(sqlite3_step(check)==SQLITE_ROW)valid=sqlite3_column_int(check,0);
    }
    sqlite3_finalize(check);return valid?0:fail(context->model,"Artwork acknowledgement invalid",200);
}
static int queue_ps4(const Ps4State *state,const unsigned char *package,size_t size,void *opaque){
    QueueContext *context=opaque;sqlite3 *memory=NULL;
    if(ps4_export_prepare(state,&memory))return fail(context->model,"PS4 trophy serialization failed",-1);
    int rc=queue_rows(memory,state->count,ps4_export_batch,opaque);sqlite3_close(memory);
    if(rc)return fail(context->model,"PS4 trophy queue failed",rc);
    if(flush_queue(context->client,context->model))return -1;
    if(!same_user())return fail(context->model,"Profile changed before PS4 artwork",-2);
    unsigned char hash[32];char digest[65],json[256],body[512],path[128];
    if(mbedtls_sha256(package,size,hash,0))return fail(context->model,"PS4 artwork digest failed",-1);
    for(unsigned i=0;i<32;i++)snprintf(digest+i*2,3,"%02x",hash[i]);
    snprintf(json,sizeof(json),"{\"title_id\":\"%s\",\"sha256\":\"%s\"}",state->title,digest);
    JsonResponse response=https_json(PROBE_IP,PROBE_PORT,PROBE_IP,PROBE_CA,"/api/device/ps4-artwork/check",context->client->device_token,json,body,sizeof(body));
    if(response.tls.rc||!response.tls.verified_handshake||response.tls.verify_flags||response.status!=200)return fail_response(context->model,"PS4 artwork check",&response);
    if(sqlite3_open(":memory:",&memory))return fail(context->model,"PS4 artwork response failed",-1);
    sqlite3_stmt *q=NULL;int needed=-1;
    const char *sql="SELECT json_extract(?1,'$.needed') WHERE json_valid(?1) AND json_type(?1,'$.needed') IN ('true','false') AND NOT EXISTS(SELECT 1 FROM json_tree(?1) GROUP BY fullkey HAVING count(*)>1)";
    if(!sqlite3_prepare_v2(memory,sql,-1,&q,NULL)){sqlite3_bind_text(q,1,body,-1,SQLITE_STATIC);if(sqlite3_step(q)==SQLITE_ROW)needed=sqlite3_column_int(q,0);}
    sqlite3_finalize(q);q=NULL;if(needed<0){sqlite3_close(memory);return fail(context->model,"PS4 artwork check invalid",200);}if(!needed){sqlite3_close(memory);return 0;}
    if(!same_user()){sqlite3_close(memory);return fail(context->model,"Profile changed before PS4 upload",-2);}
    snprintf(context->model->error,sizeof(context->model->error),"Uploading PS4 artwork and translations: %s",state->title);publish(context->model);
    snprintf(path,sizeof(path),"/api/device/ps4-artwork/%s",state->title);
    response=https_binary(PROBE_IP,PROBE_PORT,PROBE_IP,PROBE_CA,path,context->client->device_token,package,size,body,sizeof(body));
    if(response.tls.rc||!response.tls.verified_handshake||response.tls.verify_flags||response.status!=200){sqlite3_close(memory);return fail_response(context->model,"PS4 artwork upload",&response);}
    int valid=0;sql="SELECT json_extract(?1,'$.status')='stored' AND json_extract(?1,'$.title_id')=?2 AND json_extract(?1,'$.sha256')=?3 WHERE json_valid(?1) AND NOT EXISTS(SELECT 1 FROM json_tree(?1) GROUP BY fullkey HAVING count(*)>1)";
    if(!sqlite3_prepare_v2(memory,sql,-1,&q,NULL)){sqlite3_bind_text(q,1,body,-1,SQLITE_STATIC);sqlite3_bind_text(q,2,state->title,-1,SQLITE_STATIC);sqlite3_bind_text(q,3,digest,-1,SQLITE_STATIC);if(sqlite3_step(q)==SQLITE_ROW)valid=sqlite3_column_int(q,0);}
    sqlite3_finalize(q);sqlite3_close(memory);
    return valid&&same_user()?0:fail(context->model,"PS4 artwork acknowledgement invalid",200);
}
static int queue_application_artwork(const unsigned char *image,size_t size,const char *title,void *opaque){
    QueueContext *context=opaque;
    if(!same_user())return fail(context->model,"Profile changed before application artwork",-2);
    unsigned char hash[32];char digest[65],json[256],body[512],path[128];
    if(mbedtls_sha256(image,size,hash,0))return fail(context->model,"Application artwork digest failed",-1);
    for(unsigned i=0;i<32;i++)snprintf(digest+i*2,3,"%02x",hash[i]);
    snprintf(json,sizeof(json),"{\"title_id\":\"%s\",\"sha256\":\"%s\"}",title,digest);
    JsonResponse response=https_json(PROBE_IP,PROBE_PORT,PROBE_IP,PROBE_CA,"/api/device/application-artwork/check",context->client->device_token,json,body,sizeof(body));
    if(response.tls.rc||!response.tls.verified_handshake||response.tls.verify_flags||response.status!=200)return fail_response(context->model,"Application artwork check",&response);
    sqlite3 *memory=NULL;sqlite3_stmt *query=NULL;int needed=-1;
    if(sqlite3_open(":memory:",&memory))return fail(context->model,"Application artwork response failed",-1);
    const char *sql="SELECT json_extract(?1,'$.needed') WHERE json_valid(?1) AND json_type(?1,'$.needed') IN ('true','false') AND NOT EXISTS(SELECT 1 FROM json_tree(?1) GROUP BY fullkey HAVING count(*)>1)";
    if(!sqlite3_prepare_v2(memory,sql,-1,&query,NULL)){
        sqlite3_bind_text(query,1,body,-1,SQLITE_STATIC);if(sqlite3_step(query)==SQLITE_ROW)needed=sqlite3_column_int(query,0);
    }
    sqlite3_finalize(query);query=NULL;
    if(needed<0){sqlite3_close(memory);return fail(context->model,"Application artwork check invalid",200);}
    if(!needed){sqlite3_close(memory);return 0;}
    if(!same_user()){sqlite3_close(memory);return fail(context->model,"Profile changed before application artwork upload",-2);}
    snprintf(context->model->error,sizeof(context->model->error),"Uploading application artwork: %s",title);publish(context->model);
    snprintf(path,sizeof(path),"/api/device/application-artwork/%s",title);
    response=https_binary(PROBE_IP,PROBE_PORT,PROBE_IP,PROBE_CA,path,context->client->device_token,image,size,body,sizeof(body));
    if(response.tls.rc||!response.tls.verified_handshake||response.tls.verify_flags||response.status!=200){sqlite3_close(memory);return fail_response(context->model,"Application artwork upload",&response);}
    int valid=0;
    sql="SELECT json_extract(?1,'$.status')='stored' AND json_extract(?1,'$.title_id')=?2 AND json_extract(?1,'$.sha256')=?3 WHERE json_valid(?1) AND NOT EXISTS(SELECT 1 FROM json_tree(?1) GROUP BY fullkey HAVING count(*)>1)";
    if(!sqlite3_prepare_v2(memory,sql,-1,&query,NULL)){
        sqlite3_bind_text(query,1,body,-1,SQLITE_STATIC);sqlite3_bind_text(query,2,title,-1,SQLITE_STATIC);sqlite3_bind_text(query,3,digest,-1,SQLITE_STATIC);
        if(sqlite3_step(query)==SQLITE_ROW)valid=sqlite3_column_int(query,0);
    }
    sqlite3_finalize(query);sqlite3_close(memory);
    return valid&&same_user()?0:fail(context->model,"Application artwork acknowledgement invalid",200);
}
static void *network_worker(void *unused){
    (void)unused;UiModel model;pthread_mutex_lock(&lock);model=published;pthread_mutex_unlock(&lock);
    PairClient client;memset(&client,0,sizeof(client));client.directory=-1;sqlite3 *activity_memory=NULL;
    mbedtls_entropy_context entropy;mbedtls_ctr_drbg_context rng;mbedtls_entropy_init(&entropy);mbedtls_ctr_drbg_init(&rng);
    if(!same_user()||!pair_start(&client,&model,selected,now_ms())){publish(&model);goto done;}
    publish(&model);
    while(same_user()&&model.phase==UI_PAIRING){pair_tick(&client,&model,now_ms());publish(&model);sceKernelUsleep(100000);}
    if(!same_user()||model.phase!=UI_CONNECTED)goto done;
    if(flush_queue(&client,&model))goto done;
    const unsigned char label[]="ps5-native-sync-batch-v2";
    if(mbedtls_ctr_drbg_seed(&rng,mbedtls_entropy_func,&entropy,label,sizeof(label)-1)){fail(&model,"Batch randomness",-1);goto done;}
    QueueContext context={&client,&model,&rng,0};
    NativeActivityCounts activity_counts;
    snprintf(model.error,sizeof(model.error),"Reading native game foreground sessions...");publish(&model);
    int rc=native_activity_collect("/system_data/priv/system_logger2/nobackup/database/sl2_log.db",selected,&activity_memory,&activity_counts);
    if(rc){fail(&model,"Native playtime read failed",rc);goto done;}
    if(activity_counts.sessions&&queue_activity_collection(activity_memory,activity_counts.sessions,&context)){
        fail(&model,"Playtime queue failed",-1);goto done;
    }
    if(flush_queue(&client,&model))goto done;
    /* Activity is independent of trophy availability/artwork transport. */
    snprintf(model.error,sizeof(model.error),"Reading the selected profile's native trophies...");publish(&model);
    NativeCollected counts;
    rc=native_collect_assets(selected,&counts,queue_assets,&context);
    snprintf(model.reader_status,sizeof(model.reader_status),"Native: %u sets, %u earned, %u locked, %u unknown",counts.sets,counts.earned,counts.locked,counts.unknown);publish(&model);
    if(rc){fail_collection(&model,rc);goto done;}
    if(flush_queue(&client,&model))goto done;
    NativeApplicationArtworkCounts application_artwork;
    rc=native_collect_application_artwork(selected,activity_memory,&application_artwork,queue_application_artwork,&context);
    if(rc){if(model.phase!=UI_ERROR)fail(&model,rc==-2?"Profile changed while reading application artwork":"Application artwork source read failed",rc);goto done;}
    snprintf(model.error,sizeof(model.error),"Reading selected profile PS4 trophy snapshots...");publish(&model);
    Ps4Collected ps4;rc=ps4_collect(selected,&ps4,queue_ps4,&context);
    if(rc){if(model.phase!=UI_ERROR){char action[96];snprintf(action,sizeof(action),"PS4 trophy read failed at stage %d (source %d)",ps4.stage,ps4.rc);fail(&model,rc==-2?"Profile changed while reading PS4 trophies":action,rc);}goto done;}
    snprintf(model.reader_status,sizeof(model.reader_status),"PS5 %u sets; PS4 %u sets; playtime %u complete / %u incomplete",counts.sets,ps4.sets,activity_counts.completed,activity_counts.incomplete);publish(&model);
    snprintf(model.error,sizeof(model.error),"Trophies and foreground playtime imported.");
    snprintf(model.sync_status,sizeof(model.sync_status),"Sync complete: %u batches; %u app images. %u missing / %u rejected sets",context.queued,application_artwork.found,counts.missing+ps4.missing,counts.rejected+ps4.rejected);publish(&model);
done:
    sqlite3_close(activity_memory);
    if(client.directory>=0)close(client.directory);
    mbedtls_platform_zeroize(&client,sizeof(client));mbedtls_ctr_drbg_free(&rng);mbedtls_entropy_free(&entropy);return NULL;
}
int main(void){
    if(geteuid()!=0||sceUserServiceInitialize(NULL)||sceUserServiceGetForegroundUser(&selected)||selected==UINT32_MAX||pthread_mutex_init(&lock,NULL))return 1;
    memset(&published,0,sizeof(published));published.close_with_shell=true;
    snprintf(published.profile,sizeof(published.profile),"Local profile %08X",selected);
    snprintf(published.public_origin,sizeof(published.public_origin),"%s",PROBE_ORIGIN);
    snprintf(published.error,sizeof(published.error),"Starting the console sync worker...");
    snprintf(published.sync_status,sizeof(published.sync_status),"Sync: waiting for the foreground app");
    int listener=socket(AF_INET,SOCK_STREAM,0);if(listener<0)return 2;
    if(listener>=FD_SETSIZE){close(listener);return 2;}
    struct sockaddr_in address={0};
#ifdef PS5_DIAGNOSTIC_SOCKET
    address.sin_len=sizeof(address);
#endif
    address.sin_family=AF_INET;address.sin_port=htons(WORKER_STATUS_PORT);address.sin_addr.s_addr=htonl(WORKER_LOOPBACK_ADDRESS);
    if(bind(listener,(struct sockaddr*)&address,sizeof(address))||listen(listener,4)){close(listener);return 3;}
    uint64_t began=now_ms(),last_peer=began;int started=0;pthread_t thread;
    while(same_user()&&now_ms()-began<900000&&now_ms()-last_peer<(started?35000:20000)){
        fd_set readable;FD_ZERO(&readable);FD_SET(listener,&readable);struct timeval wait={0,200000};
        if(select(listener+1,&readable,NULL,NULL,&wait)!=1)continue;
        struct sockaddr_in peer_address={0};socklen_t size=sizeof(peer_address);int peer=accept(listener,(struct sockaddr*)&peer_address,&size);if(peer<0)continue;
        struct timeval timeout={2,0};WorkerRequest request;WorkerStatus status={.magic="PS5ST1",.version=1,.profile=selected};
        int valid=peer_address.sin_addr.s_addr==htonl(WORKER_LOOPBACK_ADDRESS)&&!setsockopt(peer,SOL_SOCKET,SO_RCVTIMEO,&timeout,sizeof(timeout))&&!setsockopt(peer,SOL_SOCKET,SO_SNDTIMEO,&timeout,sizeof(timeout))&&
            !worker_transfer(peer,&request,sizeof(request),0)&&!memcmp(request.magic,"PS5UI1\0",8)&&!request.reserved&&request.profile==selected&&same_user();
        if(valid){
            last_peer=now_ms();
            if(!started){
                pthread_attr_t attributes;int ok=!pthread_attr_init(&attributes);
                if(ok){size_t stack=0;int rc=pthread_attr_setstacksize(&attributes,1024*1024);if(!rc)rc=pthread_attr_getstacksize(&attributes,&stack);if(!rc&&stack<1024*1024)rc=-1;if(!rc)rc=pthread_create(&thread,&attributes,network_worker,NULL);pthread_attr_destroy(&attributes);if(!rc){started=1;pthread_detach(thread);}else valid=0;}
                else valid=0;
            }
            pthread_mutex_lock(&lock);status.model=published;pthread_mutex_unlock(&lock);
            if(status.model.phase==UI_PAIRING){uint64_t now=now_ms();if(status.model.expires_at_ms>now)status.ttl_seconds=(unsigned)((status.model.expires_at_ms-now)/1000);if(!status.ttl_seconds){status.model.phase=UI_ERROR;status.model.manual_code[0]=0;}}
            status.model.expires_at_ms=0;
            if(valid&&same_user())(void)worker_transfer(peer,&status,sizeof(status),1);
        }
        close(peer);
    }
    atomic_store(&stopping,1);close(listener);return 0;
}
