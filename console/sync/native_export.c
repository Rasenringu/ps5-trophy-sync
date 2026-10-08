/* SPDX-License-Identifier: GPL-3.0-or-later */
#define _GNU_SOURCE 1
#include "native_export.h"
#include <inttypes.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
typedef struct {sqlite3 *db;const NativeDefinitions *definitions;unsigned ordinal;} ExportContext;
static int visit(const NativeDefinition *definition,const NativeStateRecord *state,void *opaque){
    ExportContext *context=opaque;sqlite3_stmt *query=NULL;int rc=-1;
    const char *grade=definition->grade=='B'?"bronze":definition->grade=='S'?"silver":definition->grade=='G'?"gold":definition->grade=='P'?"platinum":"unknown";
    char first[24],second[24],stamp[40]={0};
    snprintf(first,sizeof(first),"%"PRIu64,state->raw_time_first);snprintf(second,sizeof(second),"%"PRIu64,state->raw_time_second);
    if(state->status==NATIVE_STATE_EARNED){
        time_t seconds=(time_t)(state->time_first_us/1000000);struct tm utc;
        if(!gmtime_r(&seconds,&utc)||!strftime(stamp,sizeof(stamp),"%Y-%m-%dT%H:%M:%S",&utc))return -1;
        size_t length=strlen(stamp);snprintf(stamp+length,sizeof(stamp)-length,".%06uZ",(unsigned)(state->time_first_us%1000000));
    }
    const char *sql="INSERT INTO exported SELECT ?1,json_object('title_id',?2,'title',?3,'trophy_id',?4,'name',?5,'grade',?6,'unlocked',json(?7),'unlocked_at',?8,'clock',?9,'native_observation',json_object('raw_flags',?10,'first_raw',?11,'second_raw',?12)) WHERE length(?3) BETWEEN 1 AND 200 AND length(?5) BETWEEN 1 AND 200";
    if(sqlite3_prepare_v2(context->db,sql,-1,&query,NULL))return -1;
    sqlite3_bind_int(query,1,(int)context->ordinal);sqlite3_bind_text(query,2,context->definitions->npwr,-1,SQLITE_STATIC);
    sqlite3_bind_text(query,3,context->definitions->title,-1,SQLITE_STATIC);sqlite3_bind_text(query,4,definition->id,-1,SQLITE_STATIC);
    sqlite3_bind_text(query,5,definition->name,-1,SQLITE_STATIC);sqlite3_bind_text(query,6,grade,-1,SQLITE_STATIC);
    sqlite3_bind_text(query,7,state->status==NATIVE_STATE_EARNED?"true":state->status==NATIVE_STATE_LOCKED?"false":"null",-1,SQLITE_STATIC);
    if(stamp[0])sqlite3_bind_text(query,8,stamp,-1,SQLITE_STATIC);else sqlite3_bind_null(query,8);
    sqlite3_bind_text(query,9,stamp[0]?"uncertain":"unknown",-1,SQLITE_STATIC);
    sqlite3_bind_int64(query,10,state->raw_flags);sqlite3_bind_text(query,11,first,-1,SQLITE_STATIC);sqlite3_bind_text(query,12,second,-1,SQLITE_STATIC);
    if(sqlite3_step(query)==SQLITE_DONE&&sqlite3_changes(context->db)==1){context->ordinal++;rc=0;}
    sqlite3_finalize(query);return rc;
}
int native_export_prepare(const NativeDefinitions *definitions,const NativeState *state,sqlite3 **output){
    if(!output)return -1;
    *output=NULL;sqlite3 *db=NULL;
    if(sqlite3_open(":memory:",&db))goto fail;
    sqlite3_limit(db,SQLITE_LIMIT_LENGTH,65536);sqlite3_db_config(db,SQLITE_DBCONFIG_TRUSTED_SCHEMA,0,NULL);
    if(sqlite3_exec(db,"CREATE TABLE exported(ordinal INTEGER PRIMARY KEY,body TEXT NOT NULL)",NULL,NULL,NULL))goto fail;
    ExportContext context={db,definitions,0};
    if(native_join(definitions,state,visit,&context)||context.ordinal!=state->count)goto fail;
    *output=db;return 0;
fail:sqlite3_close(db);return -1;
}
int native_export_batch(sqlite3 *db,const char *uuid,unsigned first,unsigned count,char output[8193]){
    if(!db||!uuid||strlen(uuid)!=36||!output||!count||count>16||first>1000||first+count>1000)return -1;
    output[0]=0;sqlite3_stmt *query=NULL;int rc=-1;
    const char *sql="SELECT json_object('schema_version',2,'batch_id',?1,'source','ps5_native','mock',json('false'),'consistency','stable_read_not_atomic','profile_binding','foreground_user_path_scoped','activities',json('[]'),'trophies',json_group_array(json(body))),count(*) FROM (SELECT body FROM exported WHERE ordinal>=?2 AND ordinal<?3 ORDER BY ordinal)";
    if(sqlite3_prepare_v2(db,sql,-1,&query,NULL))return -1;
    sqlite3_bind_text(query,1,uuid,-1,SQLITE_STATIC);sqlite3_bind_int(query,2,(int)first);sqlite3_bind_int(query,3,(int)(first+count));
    if(sqlite3_step(query)==SQLITE_ROW&&sqlite3_column_int(query,1)==(int)count){
        const unsigned char *text=sqlite3_column_text(query,0);int size=sqlite3_column_bytes(query,0);
        if(text&&size>0&&size<=8192){memcpy(output,text,(size_t)size);output[size]=0;rc=0;}
    }
    sqlite3_finalize(query);return rc;
}
