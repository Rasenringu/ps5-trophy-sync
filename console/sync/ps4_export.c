/* SPDX-License-Identifier: GPL-3.0-or-later */
#define _POSIX_C_SOURCE 200809L
#include "ps4_export.h"
#include <inttypes.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
int ps4_export_prepare(const Ps4State *state,sqlite3 **out){
    if(!out)return -1;*out=NULL;
    if(!state||!state->records||!state->count||state->count>2000||state->application_count>16)return -1;
    if(state->title[12]||strncmp(state->title,"NPWR",4)||strcmp(state->title+9,"_00"))return -1;
    for(unsigned i=4;i<9;i++)if(state->title[i]<'0'||state->title[i]>'9')return -1;
    for(unsigned i=0;i<state->application_count;i++){
        if(state->applications[i][9]||strncmp(state->applications[i],"CUSA",4))return -1;
        for(unsigned j=4;j<9;j++)if(state->applications[i][j]<'0'||state->applications[i][j]>'9')return -1;
    }
    for(unsigned i=0;i<state->count;i++){
        const Ps4StateRecord *r=state->records+i;
        int earned=r->raw_state==1&&r->raw_aux==0x2000;
        int locked=!r->raw_state&&!r->raw_aux&&!r->first_raw&&!r->second_raw;
        if(r->id!=i||r->grade<1||r->grade>4||r->unlocked!=(earned?1:locked?0:-1))return -1;
    }
    sqlite3 *db=NULL;sqlite3_stmt *q=NULL;char applications[256]="[",digest[41];size_t used=1;
    for(unsigned i=0;i<state->application_count;i++)used+=(size_t)snprintf(applications+used,sizeof(applications)-used,"%s\"%s\"",i?",":"",state->applications[i]);
    snprintf(applications+used,sizeof(applications)-used,"]");
    for(unsigned i=0;i<20;i++)snprintf(digest+i*2,3,"%02x",state->package_sha1[i]);
    if(sqlite3_open(":memory:",&db))goto fail;
    sqlite3_limit(db,SQLITE_LIMIT_LENGTH,65536);sqlite3_db_config(db,SQLITE_DBCONFIG_TRUSTED_SCHEMA,0,NULL);
    if(sqlite3_exec(db,"CREATE TABLE exported(ordinal INTEGER PRIMARY KEY,body TEXT NOT NULL)",NULL,NULL,NULL))goto fail;
    const char *sql="INSERT INTO exported SELECT ?1,json_object('title_id',?2,'title',?2,'trophy_id',?3,'name',?4,'grade',?5,'unlocked',json(?6),'unlocked_at',?7,'clock',?8,'ps4_observation',json_object('raw_state',?9,'raw_aux',?10,'raw_grade',?11,'first_raw',?12,'second_raw',?13,'trp_sha1',?14,'application_title_ids',json(?15)))";
    if(sqlite3_prepare_v2(db,sql,-1,&q,NULL))goto fail;
    for(unsigned i=0;i<state->count;i++){
        const Ps4StateRecord *r=state->records+i;char id[16],label[32],first[24],second[24],stamp[40]={0};
        snprintf(id,sizeof(id),"%u",r->id);snprintf(label,sizeof(label),"Trophy %u",r->id);
        snprintf(first,sizeof(first),"%"PRIu64,r->first_raw);snprintf(second,sizeof(second),"%"PRIu64,r->second_raw);
        /* Candidate RTC year-1 microseconds, explicitly uncertain; raw values
         * always preserved, including missing/out-of-range fields. */
        if(r->unlocked==1&&r->first_raw>=62135596800000000ULL&&r->first_raw<=315537897599999999ULL){
            uint64_t us=r->first_raw-62135596800000000ULL;time_t seconds=(time_t)(us/1000000);struct tm utc;
            if(gmtime_r(&seconds,&utc)&&strftime(stamp,sizeof(stamp),"%Y-%m-%dT%H:%M:%S",&utc)){
                size_t n=strlen(stamp);snprintf(stamp+n,sizeof(stamp)-n,".%06uZ",(unsigned)(us%1000000));
            }
        }
        const char *grade=r->grade==1?"platinum":r->grade==2?"gold":r->grade==3?"silver":"bronze";
        sqlite3_bind_int(q,1,(int)i);sqlite3_bind_text(q,2,state->title,-1,SQLITE_STATIC);sqlite3_bind_text(q,3,id,-1,SQLITE_TRANSIENT);
        sqlite3_bind_text(q,4,label,-1,SQLITE_TRANSIENT);sqlite3_bind_text(q,5,grade,-1,SQLITE_STATIC);sqlite3_bind_text(q,6,r->unlocked==1?"true":r->unlocked==0?"false":"null",-1,SQLITE_STATIC);
        if(stamp[0])sqlite3_bind_text(q,7,stamp,-1,SQLITE_TRANSIENT);else sqlite3_bind_null(q,7);
        sqlite3_bind_text(q,8,stamp[0]?"uncertain":"unknown",-1,SQLITE_STATIC);sqlite3_bind_int64(q,9,r->raw_state);sqlite3_bind_int64(q,10,r->raw_aux);
        sqlite3_bind_int(q,11,(int)r->grade);sqlite3_bind_text(q,12,first,-1,SQLITE_TRANSIENT);sqlite3_bind_text(q,13,second,-1,SQLITE_TRANSIENT);
        sqlite3_bind_text(q,14,digest,-1,SQLITE_STATIC);sqlite3_bind_text(q,15,applications,-1,SQLITE_STATIC);
        if(sqlite3_step(q)!=SQLITE_DONE)goto fail;sqlite3_reset(q);sqlite3_clear_bindings(q);
    }
    sqlite3_finalize(q);*out=db;return 0;
fail:sqlite3_finalize(q);sqlite3_close(db);return -1;
}
int ps4_export_batch(sqlite3 *db,const char *uuid,unsigned first,unsigned count,char out[8193]){
    if(!db||!uuid||strlen(uuid)!=36||!out||!count||count>16||first>2000||count>2000-first)return -1;
    sqlite3_stmt *q=NULL;int rc=-1;
    const char *sql="SELECT json_object('schema_version',4,'batch_id',?1,'source','ps4_bc','mock',json('false'),'consistency','stable_encrypted_image_copy','profile_binding','inner_local_user_and_foreground_path','activities',json('[]'),'trophies',json_group_array(json(body))),count(*) FROM (SELECT body FROM exported WHERE ordinal>=?2 AND ordinal<?3 ORDER BY ordinal)";
    if(sqlite3_prepare_v2(db,sql,-1,&q,NULL))return -1;
    sqlite3_bind_text(q,1,uuid,-1,SQLITE_STATIC);sqlite3_bind_int(q,2,(int)first);sqlite3_bind_int(q,3,(int)(first+count));
    if(sqlite3_step(q)==SQLITE_ROW&&sqlite3_column_int(q,1)==(int)count){const unsigned char *text=sqlite3_column_text(q,0);int n=sqlite3_column_bytes(q,0);if(text&&n>0&&n<=8192){memcpy(out,text,(size_t)n);out[n]=0;rc=0;}}
    sqlite3_finalize(q);return rc;
}
