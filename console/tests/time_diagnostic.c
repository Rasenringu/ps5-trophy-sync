/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Explicitly authorized one-shot only: locked read-only native logger query.
 * No mounts, imports, credential reads or source writes. Own report only. */
#define _POSIX_C_SOURCE 200809L
#include "../readers/schema_probe.h"
#include <sqlite3.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>
extern int sceUserServiceInitialize(void *);
extern int sceUserServiceGetForegroundUser(uint32_t *);
int __patch_init(void){return 0;}
static unsigned selected;
static int budget(void *opaque){
    struct timespec stamp;uint32_t profile=UINT32_MAX;
    return clock_gettime(CLOCK_MONOTONIC,&stamp)||stamp.tv_sec>=*(time_t*)opaque||
        sceUserServiceGetForegroundUser(&profile)||profile!=selected;
}
int main(void){
    if(geteuid()!=0||sceUserServiceInitialize(NULL)||sceUserServiceGetForegroundUser(&selected)||selected==UINT32_MAX)return 1;
    int fd=open("/data/trophy-sync-time-report.txt",O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC,0600);
    if(fd<0)return 2;
    struct stat st;if(fstat(fd,&st)||!S_ISREG(st.st_mode)||st.st_uid!=geteuid()||(st.st_mode&077)){close(fd);return 3;}
    FILE *report=fdopen(fd,"w");if(!report){close(fd);return 4;}
    fprintf(report,"TrophySync read-only clock/counter diagnostic v1\nNo profile/session/account identifiers, credentials or raw logs.\nconsole_unix_seconds=%lld\n",(long long)time(NULL));
    const char *path="/system_data/priv/system_logger2/nobackup/database/sl2_log.db";
    SchemaProbe probe=schema_probe(path);sqlite3 *db=NULL;sqlite3_stmt *q=NULL;int result=5;
    fprintf(report,"logger_rc=%d journal=%s\n",probe.rc,probe.journal_mode);
    if(probe.rc||strcmp(probe.journal_mode,"delete"))goto done;
    if(sqlite3_open_v2(path,&db,SQLITE_OPEN_READONLY|SQLITE_OPEN_NOFOLLOW,"ps5-sync-deny-write")||sqlite3_db_readonly(db,"main")!=1)goto done;
    sqlite3_busy_timeout(db,250);sqlite3_limit(db,SQLITE_LIMIT_LENGTH,65536);
    sqlite3_db_config(db,SQLITE_DBCONFIG_TRUSTED_SCHEMA,0,NULL);sqlite3_db_config(db,SQLITE_DBCONFIG_DEFENSIVE,1,NULL);
    struct timespec start;if(clock_gettime(CLOCK_MONOTONIC,&start))goto done;time_t deadline=start.tv_sec+5;
    sqlite3_progress_handler(db,100,budget,&deadline);
    if(sqlite3_exec(db,"PRAGMA query_only=ON; BEGIN",NULL,NULL,NULL))goto done;
    const char *sql="SELECT json_extract(log,'$.appTitleId'),event_id,count(*),"
        "sum(json_type(log,'$.fgTime')='integer'),sum(json_type(log,'$.fgTime') IS NULL),"
        "min(strftime('%Y-%m-%dT%H:%M:%f',created_date)),max(strftime('%Y-%m-%dT%H:%M:%f',created_date)),"
        "sum(created_date LIKE '%Z' OR substr(created_date,-6,1) IN ('+','-')) "
        "FROM tbl_log WHERE event_id IN ('ApplicationSessionStart','ApplicationSessionEnd','ApplicationSessionEndBi','ApplicationSessionCrash') "
        "AND length(log)<16384 AND length(log_header)<8192 AND json_valid(log) AND json_valid(log_header) "
        "AND json_type(log_header,'$.localUserIds')='array' AND json_array_length(log_header,'$.localUserIds')=1 "
        "AND lower(json_extract(log_header,'$.localUserIds[0]'))=?1 "
        "AND (json_extract(log,'$.appTitleId') GLOB 'PPSA[0-9][0-9][0-9][0-9][0-9]' OR json_extract(log,'$.appTitleId') GLOB 'CUSA[0-9][0-9][0-9][0-9][0-9]') "
        "GROUP BY 1,2 ORDER BY 1,2 LIMIT 256";
    if(sqlite3_prepare_v2(db,sql,-1,&q,NULL))goto done;
    char profile[9];snprintf(profile,sizeof(profile),"%08x",selected);sqlite3_bind_text(q,1,profile,-1,SQLITE_STATIC);
    int step;
    while((step=sqlite3_step(q))==SQLITE_ROW){
        if(budget(&deadline))goto done;
        fprintf(report,"title=%s event=%s rows=%d integer_fg=%d absent_fg=%d first_candidate=%s last_candidate=%s explicit_offset_rows=%d\n",
            sqlite3_column_text(q,0),sqlite3_column_text(q,1),sqlite3_column_int(q,2),sqlite3_column_int(q,3),sqlite3_column_int(q,4),
            sqlite3_column_type(q,5)==SQLITE_TEXT?(const char*)sqlite3_column_text(q,5):"unavailable",
            sqlite3_column_type(q,6)==SQLITE_TEXT?(const char*)sqlite3_column_text(q,6):"unavailable",sqlite3_column_int(q,7));
    }
    if(step==SQLITE_DONE&&!budget(&deadline))result=0;
done:
    sqlite3_finalize(q);if(db){sqlite3_exec(db,"ROLLBACK",NULL,NULL,NULL);sqlite3_close(db);}
    fprintf(report,"diagnostic_result=%d\n",result);
    if(ferror(report)||fflush(report)||fsync(fd))result=6;
    if(fclose(report))result=6;
    return result;
}
