/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "client.h"
#include "state.h"
#include "../transport/https_json.h"
#include "probe_config.h"
#include <sqlite3.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
#ifndef PAIR_STATE_DIRECTORY
#define PAIR_STATE_DIRECTORY "/data/trophy-sync-live"
#endif

typedef struct {char id[37],secret[129],origin[192];} Installation;
typedef struct {unsigned profile;char uuid[37],token[129];} Profile;
static void (*progress_hook)(unsigned);
void pair_set_progress(void (*progress)(unsigned stage)){progress_hook=progress;}
static void progress(unsigned stage){if(progress_hook)progress_hook(stage);}
static int safe_secret(const char *s) {
    size_t n=strlen(s);if(n<32||n>128)return 0;
    for(;*s;s++)if(!((*s>='A'&&*s<='Z')||(*s>='a'&&*s<='z')||(*s>='0'&&*s<='9')||*s=='_'||*s=='-'))return 0;
    return 1;
}
static int safe_uuid(const char *s) {
    if(strlen(s)!=36)return 0;
    for(int i=0;i<36;i++)if(i==8||i==13||i==18||i==23){if(s[i]!='-')return 0;}else if(!((s[i]>='0'&&s[i]<='9')||(s[i]>='a'&&s[i]<='f')))return 0;
    return 1;
}
static void error(UiModel *ui,const char *action,int code) {
    ui->phase=UI_ERROR;ui->manual_code[0]=0;
    snprintf(ui->error,sizeof(ui->error),"%s failed (%d). Close App and retry.",action,code);
}
static void storage_error(UiModel *ui,const char *phase){
    char action[100];snprintf(action,sizeof(action),"%s: %s",phase,state_error_operation());
    error(ui,action,state_error_code());
}
/* Dedicated bounded in-memory JSON only, never an activity/system DB. */
static sqlite3 *json_open(const char *body) {
    sqlite3 *db=NULL;sqlite3_stmt *s=NULL;
    if(sqlite3_open(":memory:",&db)!=SQLITE_OK)goto fail;
    sqlite3_limit(db,SQLITE_LIMIT_LENGTH,16384);
    sqlite3_db_config(db,SQLITE_DBCONFIG_TRUSTED_SCHEMA,0,NULL);
    if(sqlite3_prepare_v2(db,"SELECT json_valid(?1) AND json_type(?1)='object'",-1,&s,NULL))goto fail;
    sqlite3_bind_text(s,1,body,-1,SQLITE_TRANSIENT);
    if(sqlite3_step(s)!=SQLITE_ROW||!sqlite3_column_int(s,0))goto fail;
    sqlite3_finalize(s);s=NULL;
    if(sqlite3_prepare_v2(db,"SELECT 1 FROM json_tree(?1) GROUP BY fullkey HAVING count(*)>1 LIMIT 1",-1,&s,NULL))goto fail;
    sqlite3_bind_text(s,1,body,-1,SQLITE_TRANSIENT);
    if(sqlite3_step(s)!=SQLITE_DONE)goto fail;
    sqlite3_finalize(s);return db;
fail:
    sqlite3_finalize(s);sqlite3_close(db);return NULL;
}
static int field(sqlite3 *db,const char *body,const char *key,char *out,size_t capacity) {
    sqlite3_stmt *s=NULL;int ok=0;
    if(sqlite3_prepare_v2(db,"SELECT json_extract(?1,?2),json_type(?1,?2)",-1,&s,NULL))return 0;
    sqlite3_bind_text(s,1,body,-1,SQLITE_TRANSIENT);sqlite3_bind_text(s,2,key,-1,SQLITE_TRANSIENT);
    if(sqlite3_step(s)==SQLITE_ROW){
        const char *p=(const char*)sqlite3_column_text(s,0),*type=(const char*)sqlite3_column_text(s,1);
        int n=sqlite3_column_bytes(s,0);
        if(p&&type&&!strcmp(type,"text")&&n>0&&(size_t)n<capacity&&!memchr(p,0,(size_t)n)){
            memcpy(out,p,(size_t)n);out[n]=0;ok=1;
        }
    }
    sqlite3_finalize(s);return ok;
}
static long long number(sqlite3 *db,const char *body,const char *key) {
    sqlite3_stmt *s=NULL;long long n=-1;
    if(sqlite3_prepare_v2(db,"SELECT json_extract(?1,?2),json_type(?1,?2)",-1,&s,NULL))return -1;
    sqlite3_bind_text(s,1,body,-1,SQLITE_TRANSIENT);sqlite3_bind_text(s,2,key,-1,SQLITE_TRANSIENT);
    if(sqlite3_step(s)==SQLITE_ROW){const char *type=(const char*)sqlite3_column_text(s,1);if(type&&!strcmp(type,"integer"))n=sqlite3_column_int64(s,0);}
    sqlite3_finalize(s);return n;
}
static int request(UiModel *ui,const char *path,const char *token,const char *input,char output[16384]) {
    JsonResponse r=https_json(PROBE_IP,PROBE_PORT,PROBE_IP,PROBE_CA,path,token,input,output,16384);
    if(r.tls.rc){error(ui,"HTTPS",r.tls.rc);return 0;}
    if(r.status!=200&&r.status!=201){error(ui,r.status==401?"Credential revoked or invalid":"Server request",r.status);return 0;}
    return 1;
}
int pair_start(PairClient *c,UiModel *ui,unsigned profile,unsigned long long now) {
    memset(c,0,sizeof(*c));c->directory=-1;c->profile=profile;
    snprintf(c->origin,sizeof(c->origin),"https://%s:%u",PROBE_IP,PROBE_PORT);
    snprintf(ui->profile,sizeof(ui->profile),"Local profile %08X",profile);
    progress(1);c->directory=state_open(PAIR_STATE_DIRECTORY);
    if(c->directory<0){storage_error(ui,"Storage");return 0;}
    progress(2);Installation installation={0};int load=state_read(c->directory,"installation.bin",&installation,sizeof(installation));
    char body[16384];sqlite3 *db=NULL;
    if(load<0){storage_error(ui,"Installation storage");return 0;}
    if(!load){
        if(!memchr(installation.id,0,sizeof(installation.id))||!memchr(installation.secret,0,sizeof(installation.secret))||!memchr(installation.origin,0,sizeof(installation.origin))||
           !safe_uuid(installation.id)||!safe_secret(installation.secret)||strcmp(installation.origin,c->origin)){error(ui,"Installation identity",-1);return 0;}
    }else{
        progress(3);if(!request(ui,"/api/device/installations",NULL,"{}",body))return 0;
        progress(4);db=json_open(body);
        int valid=db&&field(db,body,"$.installation_id",installation.id,sizeof(installation.id))&&field(db,body,"$.installation_secret",installation.secret,sizeof(installation.secret))&&safe_uuid(installation.id)&&safe_secret(installation.secret);
        sqlite3_close(db);db=NULL;memset(body,0,sizeof(body));
        if(!valid){error(ui,"Installation response",-1);return 0;}
        snprintf(installation.origin,sizeof(installation.origin),"%s",c->origin);
        progress(5);if(state_write(c->directory,"installation.bin",&installation,sizeof(installation))){storage_error(ui,"Save installation");return 0;}
    }
    snprintf(c->installation_id,sizeof(c->installation_id),"%s",installation.id);
    snprintf(c->installation_secret,sizeof(c->installation_secret),"%s",installation.secret);memset(&installation,0,sizeof(installation));
    progress(6);Profile saved={0};char filename[32];snprintf(filename,sizeof(filename),"profile-%08x.bin",profile);
    load=state_read(c->directory,filename,&saved,sizeof(saved));
    if(load<0){storage_error(ui,"Profile credential storage");return 0;}
    if(!load){
        if(saved.profile!=profile||!memchr(saved.uuid,0,sizeof(saved.uuid))||!memchr(saved.token,0,sizeof(saved.token))||!safe_uuid(saved.uuid)||!safe_secret(saved.token)){error(ui,"Saved profile credential",-1);return 0;}
        snprintf(c->device_token,sizeof(c->device_token),"%s",saved.token);snprintf(c->profile_uuid,sizeof(c->profile_uuid),"%s",saved.uuid);memset(&saved,0,sizeof(saved));
        progress(7);if(!request(ui,"/api/device/status",c->device_token,"{}",body))return 0;
        db=json_open(body);char remote_uuid[37]={0},remote_id[64]={0},expected_id[16];
        snprintf(expected_id,sizeof(expected_id),"%08x",profile);
        int valid=db&&field(db,body,"$.profile_uuid",remote_uuid,sizeof(remote_uuid))&&field(db,body,"$.profile_id",remote_id,sizeof(remote_id))&&!strcmp(remote_uuid,c->profile_uuid)&&!strcmp(remote_id,expected_id);
        sqlite3_close(db);memset(body,0,sizeof(body));
        if(!valid){error(ui,"Saved profile ownership",-1);return 0;}
        ui->phase=UI_CONNECTED;snprintf(ui->error,sizeof(ui->error),"Saved profile verified. Unlocks/playtime unavailable.");return 1;
    }
    char input[512];snprintf(input,sizeof(input),"{\"installation_id\":\"%s\",\"profile_id\":\"%08x\",\"profile_label\":\"Local profile %08X\"}",c->installation_id,profile,profile);
    progress(7);if(!request(ui,"/api/device/pairings",c->installation_secret,input,body))return 0;
    progress(8);db=json_open(body);char code[10]={0},uri[256]={0},expected[256];
    long long expires=db?number(db,body,"$.expires_at"):-1,interval=db?number(db,body,"$.interval"):-1;
    time_t wall=time(NULL);long long ttl=expires-(long long)wall;
    int valid=db&&field(db,body,"$.device_code",c->device_code,sizeof(c->device_code))&&safe_secret(c->device_code)&&field(db,body,"$.user_code",code,sizeof(code))&&field(db,body,"$.verification_uri",uri,sizeof(uri));
    snprintf(expected,sizeof(expected),"%s/pair",c->origin);
    valid=valid&&strcmp(uri,expected)==0&&interval>=5&&interval<=60&&wall>0&&ttl>0&&ttl<=600;
    sqlite3_close(db);memset(body,0,sizeof(body));
    if(!valid||!ui_set_pairing(ui,c->origin,code,now,(unsigned)ttl)){error(ui,"Pairing response or clock",-1);return 0;}
    c->deadline_ms=ui->expires_at_ms;c->next_poll_ms=now+(unsigned long long)interval*1000;
    progress(9);
    return 1;
}
void pair_tick(PairClient *c,UiModel *ui,unsigned long long now) {
    if(ui->phase!=UI_PAIRING||now<c->next_poll_ms)return;
    if(now>=c->deadline_ms||c->attempts>=120){ui->manual_code[0]=0;error(ui,"Pairing expired",410);return;}
    c->attempts++;c->next_poll_ms=now+5000;
    char input[256],body[16384];snprintf(input,sizeof(input),"{\"device_code\":\"%s\"}",c->device_code);
    progress(10);if(!request(ui,"/api/device/pairings/poll",NULL,input,body))return;
    progress(11);sqlite3 *db=json_open(body);char status[32]={0};
    if(!db||!field(db,body,"$.status",status,sizeof(status))){sqlite3_close(db);error(ui,"Polling response",-1);return;}
    if(!strcmp(status,"pending")){sqlite3_close(db);memset(body,0,sizeof(body));return;}
    Profile profile;memset(&profile,0,sizeof(profile));profile.profile=c->profile;
    int valid=!strcmp(status,"paired")&&field(db,body,"$.device_token",profile.token,sizeof(profile.token))&&safe_secret(profile.token)&&field(db,body,"$.profile_uuid",profile.uuid,sizeof(profile.uuid))&&safe_uuid(profile.uuid);
    sqlite3_close(db);memset(body,0,sizeof(body));
    if(!valid){error(ui,"Device credential response",-1);return;}
    char filename[32];snprintf(filename,sizeof(filename),"profile-%08x.bin",c->profile);
    progress(12);if(state_write(c->directory,filename,&profile,sizeof(profile))){memset(&profile,0,sizeof(profile));storage_error(ui,"Save credential; revoke if needed");return;}
    snprintf(c->device_token,sizeof(c->device_token),"%s",profile.token);snprintf(c->profile_uuid,sizeof(c->profile_uuid),"%s",profile.uuid);
    memset(&profile,0,sizeof(profile));memset(c->device_code,0,sizeof(c->device_code));
    ui->manual_code[0]=0;ui->phase=UI_CONNECTED;
    snprintf(ui->error,sizeof(ui->error),"Profile paired. Trophy unlocks/playtime unavailable.");
}
