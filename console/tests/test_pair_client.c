/* SPDX-License-Identifier: GPL-3.0-or-later */
#define _GNU_SOURCE 1
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include "../pairing/state.h"
#include "../transport/https_json.h"
#include "probe_config.h"
static char root[]="/tmp/MOCK-pair-XXXXXX";
static time_t fake_time(time_t *out){if(out)*out=1000;return 1000;}
static int local_open(const char *path){assert(!strcmp(path,PROBE_STATE_DIRECTORY));return state_open(root);}
#define state_open local_open
#define time fake_time
#include "../pairing/client.c"
#undef state_open
#undef time
static int installs,pairings,polls,status_requests,paired_response,revoked;
JsonResponse https_json(const char *ip,unsigned short port,const char *name,const char *ca,const char *path,const char *token,const char *input,char *body,size_t capacity){
    (void)port;(void)ca;assert(!strcmp(ip,name)&&input&&capacity==16384);
    JsonResponse r={.tls={.rc=0,.verified_handshake=1},.status=200};
    if(!strcmp(path,"/api/device/installations")){
        installs++;r.status=201;
        snprintf(body,capacity,"{\"installation_id\":\"12345678-1234-1234-1234-123456789abc\",\"installation_secret\":\"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\"}");
    }else if(!strcmp(path,"/api/device/pairings")){
        pairings++;assert(token&&safe_secret(token));
        snprintf(body,capacity,"{\"device_code\":\"BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB\",\"user_code\":\"ABCD-2345\",\"verification_uri\":\"%s/pair\",\"expires_at\":1600,\"interval\":5}",PROBE_ORIGIN);
    }else if(!strcmp(path,"/api/device/pairings/poll")){
        polls++;
        snprintf(body,capacity,paired_response?"{\"status\":\"paired\",\"device_token\":\"CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC\",\"profile_uuid\":\"abcdef12-1234-1234-1234-123456789abc\"}":"{\"status\":\"pending\",\"interval\":5}");
    }else{
        assert(!strcmp(path,"/api/device/status"));status_requests++;
        if(revoked){r.status=401;snprintf(body,capacity,"{}");}
        else snprintf(body,capacity,"{\"status\":\"paired\",\"profile_uuid\":\"abcdef12-1234-1234-1234-123456789abc\",\"profile_id\":\"01020304\"}");
    }
    r.size=strlen(body);return r;
}
int main(void){
    assert(mkdtemp(root));PairClient c;UiModel ui={0};
    assert(pair_start(&c,&ui,0x01020304,100));assert(ui.phase==UI_PAIRING);
    assert(installs==1&&pairings==1&&!polls&&!status_requests);
    pair_tick(&c,&ui,5099);assert(!polls);
    pair_tick(&c,&ui,5100);assert(polls==1&&ui.phase==UI_PAIRING);
    pair_tick(&c,&ui,5101);assert(polls==1);
    paired_response=1;pair_tick(&c,&ui,10100);assert(polls==2&&ui.phase==UI_CONNECTED&&!ui.manual_code[0]);
    assert(!c.device_code[0]&&safe_secret(c.device_token));close(c.directory);
    assert(pair_start(&c,&ui,0x01020304,20000));assert(ui.phase==UI_CONNECTED&&installs==1&&pairings==1&&status_requests==1);close(c.directory);
    revoked=1;assert(!pair_start(&c,&ui,0x01020304,20001));assert(ui.phase==UI_ERROR&&strstr(ui.error,"401"));close(c.directory);
    assert(pair_start(&c,&ui,0x01020305,30000));int previous=polls;
    pair_tick(&c,&ui,c.deadline_ms);assert(ui.phase==UI_ERROR&&!ui.manual_code[0]&&polls==previous);close(c.directory);
    sqlite3 *db=json_open("{\"x\":\"one\",\"x\":\"two\"}");assert(!db);
    db=json_open("{\"x\":123,\"y\":\"a\\u0000b\"}");assert(db);char v[16];
    assert(!field(db,"{\"x\":123}","$.x",v,sizeof(v)));
    assert(!field(db,"{\"y\":\"a\\u0000b\"}","$.y",v,sizeof(v)));sqlite3_close(db);
    int dir=state_open(root);assert(dir>=0);
    assert(!unlinkat(dir,"installation.bin",0));assert(!unlinkat(dir,"profile-01020304.bin",0));close(dir);assert(!rmdir(root));
    puts("PASS MOCK pairing: real C state machine, bounded polling/expiry, persisted installation/profile isolation, saved-token check/revocation, duplicate/NUL/type JSON rejection. No console/server contacted.");
}
