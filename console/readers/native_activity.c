/* SPDX-License-Identifier: GPL-3.0-or-later */
#define _POSIX_C_SOURCE 200809L
#include "native_activity.h"
#include "schema_probe.h"
#include <mbedtls/sha256.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include <stdlib.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>
extern int sceUserServiceGetForegroundUser(uint32_t*);
static int same_user(unsigned profile){uint32_t user=UINT32_MAX;return !sceUserServiceGetForegroundUser(&user)&&user==profile;}
static int budget(void *opaque){struct timespec now;if(clock_gettime(CLOCK_MONOTONIC,&now))return 1;return now.tv_sec>=*(time_t*)opaque;}
static int title_id(const char *s){if(!s||strlen(s)!=9||strncmp(s,"PPSA",4))return 0;for(int i=4;i<9;i++)if(s[i]<'0'||s[i]>'9')return 0;return 1;}
static int project_title(const char *s){unsigned n=(unsigned)strtoul(s+4,NULL,10);return n>=99871&&n<=99889;}
static int metadata_title(sqlite3 *memory,const char *title,char output[201]){
 char path[512],body[65537];
#ifdef NATIVE_ACTIVITY_TEST
 const char *root=getenv("MOCK_METADATA_ROOT");if(!root)return -1;
#else
 const char *root="/user/appmeta";
#endif
 int size=snprintf(path,sizeof(path),"%s/%s/param.json",root,title);if(size<=0||(size_t)size>=sizeof(path))return -1;
 int fd=open(path,O_RDONLY|O_NOFOLLOW|O_CLOEXEC);if(fd<0)return -1;struct stat st;size_t at=0;int rc=-1;
 if(fstat(fd,&st)||!S_ISREG(st.st_mode)||st.st_size<2||st.st_size>65536)goto done;
 while(at<(size_t)st.st_size){ssize_t n=read(fd,body+at,(size_t)st.st_size-at);if(n<=0)goto done;at+=(size_t)n;}body[at]=0;
 struct stat after;if(fstat(fd,&after)||st.st_size!=after.st_size||st.st_mtime!=after.st_mtime)goto done;
 sqlite3_stmt *q=NULL;
 if(sqlite3_prepare_v2(memory,"SELECT json_extract(?1,'$.localizedParameters.\"en-US\".titleName') WHERE json_valid(?1) AND json_extract(?1,'$.titleId')=?2 AND NOT EXISTS(SELECT 1 FROM json_tree(?1) GROUP BY fullkey HAVING count(*)>1)",-1,&q,NULL))goto done;
 sqlite3_bind_text(q,1,body,(int)at,SQLITE_STATIC);sqlite3_bind_text(q,2,title,-1,SQLITE_STATIC);
 if(sqlite3_step(q)==SQLITE_ROW&&sqlite3_column_type(q,0)==SQLITE_TEXT){int n=sqlite3_column_bytes(q,0);if(n>0&&n<=200){memcpy(output,sqlite3_column_text(q,0),(size_t)n);output[n]=0;rc=0;}}
 sqlite3_finalize(q);
done:close(fd);return rc;
}
static int identity(const char *title,const char *session,char hash[65]){
 if(!session||!*session||strlen(session)>128)return -1;
 unsigned char input[160],bytes[32];int n=snprintf((char*)input,sizeof(input),"native-session-v1:%s:%s",title,session);
 if(n<=0||(size_t)n>=sizeof(input)||mbedtls_sha256(input,(size_t)n,bytes,0))return -1;
 for(int i=0;i<32;i++)snprintf(hash+i*2,3,"%02x",bytes[i]);return 0;
}
int native_activity_collect(const char *path,unsigned profile,sqlite3 **output,NativeActivityCounts *counts){
 if(!path||!output||!counts)return -1;*output=NULL;memset(counts,0,sizeof(*counts));if(!same_user(profile))return -2;
 SchemaProbe probe=schema_probe(path);if(probe.rc||strcmp(probe.journal_mode,"delete"))return -3;
 sqlite3 *source=NULL,*memory=NULL;sqlite3_stmt *rows=NULL,*insert=NULL;int result=-1;
 if(sqlite3_open(":memory:",&memory))goto done;
 sqlite3_limit(memory,SQLITE_LIMIT_LENGTH,131072);sqlite3_db_config(memory,SQLITE_DBCONFIG_TRUSTED_SCHEMA,0,NULL);
 if(sqlite3_exec(memory,"CREATE TABLE sessions(identity TEXT PRIMARY KEY,title_id TEXT,title TEXT,started TEXT,ended TEXT,seconds INTEGER,event TEXT); CREATE TABLE titles(id TEXT PRIMARY KEY,name TEXT)",NULL,NULL,NULL))goto done;
 if(sqlite3_open_v2(path,&source,SQLITE_OPEN_READONLY|SQLITE_OPEN_NOFOLLOW,"ps5-sync-deny-write")||sqlite3_db_readonly(source,"main")!=1)goto done;
 sqlite3_busy_timeout(source,250);sqlite3_limit(source,SQLITE_LIMIT_LENGTH,65536);
 sqlite3_db_config(source,SQLITE_DBCONFIG_TRUSTED_SCHEMA,0,NULL);sqlite3_db_config(source,SQLITE_DBCONFIG_DEFENSIVE,1,NULL);
 struct timespec start;if(clock_gettime(CLOCK_MONOTONIC,&start))goto done;time_t deadline=start.tv_sec+8;
 sqlite3_progress_handler(source,100,budget,&deadline);
 if(sqlite3_exec(source,"PRAGMA query_only=ON; BEGIN",NULL,NULL,NULL))goto done;
 const char *sql="SELECT json_extract(log,'$.appTitleId'),json_extract(log,'$.appSessionId'),event_id,"
 "strftime('%Y-%m-%dT%H:%M:%fZ',created_date),json_type(log,'$.fgTime'),json_extract(log,'$.fgTime') "
 "FROM tbl_log WHERE event_id IN ('ApplicationSessionStart','ApplicationSessionEnd','ApplicationSessionCrash') "
 "AND length(log)<16384 AND length(log_header)<8192 AND json_valid(log) AND json_valid(log_header) "
 "AND json_type(log_header,'$.localUserIds')='array' AND json_array_length(log_header,'$.localUserIds')=1 "
 "AND json_type(log_header,'$.localUserIds[0]')='text' AND length(json_extract(log_header,'$.localUserIds[0]'))=8 "
 "AND lower(json_extract(log_header,'$.localUserIds[0]'))=?1 "
 "AND NOT EXISTS(SELECT 1 FROM json_tree(log) GROUP BY fullkey HAVING count(*)>1) "
 "AND NOT EXISTS(SELECT 1 FROM json_tree(log_header) GROUP BY fullkey HAVING count(*)>1) ORDER BY rowid LIMIT 4097";
 if(sqlite3_prepare_v2(source,sql,-1,&rows,NULL))goto done;
 char hex[16];snprintf(hex,sizeof(hex),"%08x",profile);
 sqlite3_bind_text(rows,1,hex,-1,SQLITE_STATIC);
 const char *upsert="INSERT INTO sessions VALUES(?1,?2,?3,CASE WHEN ?4='ApplicationSessionStart' THEN ?5 END,CASE WHEN ?4!='ApplicationSessionStart' THEN ?5 END,?6,?4) ON CONFLICT(identity) DO UPDATE SET "
 "started=COALESCE(sessions.started,excluded.started),ended=CASE WHEN sessions.seconds IS NULL AND excluded.ended IS NOT NULL THEN excluded.ended WHEN excluded.seconds IS NOT NULL AND (sessions.seconds IS NULL OR excluded.seconds>=sessions.seconds) THEN excluded.ended ELSE sessions.ended END,"
 "seconds=CASE WHEN sessions.seconds IS NULL THEN excluded.seconds WHEN excluded.seconds IS NULL THEN sessions.seconds ELSE max(sessions.seconds,excluded.seconds) END,"
 "event=CASE WHEN sessions.seconds IS NOT NULL AND excluded.seconds IS NULL THEN sessions.event ELSE excluded.event END";
 if(sqlite3_prepare_v2(memory,upsert,-1,&insert,NULL))goto done;
 int step;
 while((step=sqlite3_step(rows))==SQLITE_ROW){
  if(++counts->rows>4096)goto done;if(!same_user(profile)){result=-2;goto done;}
  const char *title=(const char*)sqlite3_column_text(rows,0),*session=(const char*)sqlite3_column_text(rows,1),*event=(const char*)sqlite3_column_text(rows,2);
  if(!title_id(title)||project_title(title))continue;
  char hash[65],name[201];if(identity(title,session,hash)){counts->rejected++;continue;}
  sqlite3_stmt *cache=NULL;if(sqlite3_prepare_v2(memory,"SELECT name FROM titles WHERE id=?1",-1,&cache,NULL))goto done;
  sqlite3_bind_text(cache,1,title,-1,SQLITE_STATIC);int cached=sqlite3_step(cache)==SQLITE_ROW;
  if(cached)snprintf(name,sizeof(name),"%s",sqlite3_column_text(cache,0));sqlite3_finalize(cache);
  if(!cached){if(metadata_title(memory,title,name)){counts->rejected++;continue;}
   if(sqlite3_prepare_v2(memory,"INSERT INTO titles VALUES(?1,?2)",-1,&cache,NULL))goto done;
   sqlite3_bind_text(cache,1,title,-1,SQLITE_STATIC);sqlite3_bind_text(cache,2,name,-1,SQLITE_STATIC);int rc=sqlite3_step(cache);sqlite3_finalize(cache);if(rc!=SQLITE_DONE)goto done;}
  const char *type=(const char*)sqlite3_column_text(rows,4);sqlite3_int64 seconds=sqlite3_column_int64(rows,5);
  int complete=!strcmp(event,"ApplicationSessionEnd")&&type&&!strcmp(type,"integer")&&seconds>=0&&seconds<=604800;
  if(!strcmp(event,"ApplicationSessionEnd")&&!complete)counts->rejected++;
  sqlite3_reset(insert);sqlite3_clear_bindings(insert);sqlite3_bind_text(insert,1,hash,-1,SQLITE_STATIC);sqlite3_bind_text(insert,2,title,-1,SQLITE_STATIC);sqlite3_bind_text(insert,3,name,-1,SQLITE_STATIC);sqlite3_bind_text(insert,4,event,-1,SQLITE_STATIC);
  if(sqlite3_column_type(rows,3)==SQLITE_TEXT)sqlite3_bind_text(insert,5,(const char*)sqlite3_column_text(rows,3),-1,SQLITE_STATIC);
  if(complete)sqlite3_bind_int64(insert,6,seconds);if(sqlite3_step(insert)!=SQLITE_DONE)goto done;
 }
 if(step!=SQLITE_DONE||!same_user(profile))goto done;
 sqlite3_finalize(insert);insert=NULL;
 /* A trusted native duration does not require a trusted wall clock. Preserve
  * invalid/reversed intervals as unknown rather than deriving a duration. */
 const char *export_sql="CREATE TABLE exported(ordinal INTEGER PRIMARY KEY,body TEXT NOT NULL);INSERT INTO exported(body) SELECT json_object("
 "'event_id','native-session:'||identity,'title_id',title_id,'title',title,'started_at',CASE WHEN ended IS NULL OR started<=ended THEN started END,"
 "'ended_at',CASE WHEN started IS NULL OR started<=ended THEN ended END,'duration_seconds',seconds,'complete',json(CASE WHEN seconds IS NULL THEN 'false' ELSE 'true' END),"
 "'clock',CASE WHEN started IS NULL AND ended IS NULL THEN 'unknown' ELSE 'uncertain' END,'duration_basis','native_foreground_seconds',"
 "'native_observation',json_object('application_title_id',title_id,'session_digest',identity,'foreground_seconds',seconds,'event',CASE WHEN seconds IS NOT NULL THEN 'ApplicationSessionEnd' ELSE event END)) FROM sessions ORDER BY title_id,identity";
 if(sqlite3_exec(memory,export_sql,NULL,NULL,NULL))goto done;
 sqlite3_stmt *q=NULL;if(sqlite3_prepare_v2(memory,"SELECT count(*),sum(seconds IS NOT NULL),sum(seconds IS NULL) FROM sessions",-1,&q,NULL))goto done;
 if(sqlite3_step(q)==SQLITE_ROW){counts->sessions=(unsigned)sqlite3_column_int(q,0);counts->completed=(unsigned)sqlite3_column_int(q,1);counts->incomplete=(unsigned)sqlite3_column_int(q,2);}sqlite3_finalize(q);
 *output=memory;memory=NULL;result=0;
done:sqlite3_finalize(rows);sqlite3_finalize(insert);if(source){sqlite3_exec(source,"ROLLBACK",NULL,NULL,NULL);sqlite3_close(source);}sqlite3_close(memory);return result;
}
int native_activity_batch(sqlite3 *memory,const char *uuid,unsigned first,unsigned count,char output[8193]){
 if(!memory||!uuid||strlen(uuid)!=36||!count||count>16||first+count>4096||!output)return -1;
 sqlite3_stmt *q=NULL;int rc=-1;output[0]=0;
 const char *sql="SELECT json_object('schema_version',3,'batch_id',?1,'source','ps5_native','mock',json('false'),'consistency','sqlite_read_transaction','profile_binding','activity_header_single_local_user','trophies',json('[]'),'activities',json_group_array(json(body))),count(*) FROM (SELECT body FROM exported WHERE ordinal>?2 AND ordinal<=?3 ORDER BY ordinal)";
 if(sqlite3_prepare_v2(memory,sql,-1,&q,NULL))return -1;sqlite3_bind_text(q,1,uuid,-1,SQLITE_STATIC);sqlite3_bind_int(q,2,(int)first);sqlite3_bind_int(q,3,(int)(first+count));
 if(sqlite3_step(q)==SQLITE_ROW&&sqlite3_column_int(q,1)==(int)count){int size=sqlite3_column_bytes(q,0);if(size>0&&size<=8192){memcpy(output,sqlite3_column_text(q,0),(size_t)size);output[size]=0;rc=0;}}
 sqlite3_finalize(q);return rc;
}
