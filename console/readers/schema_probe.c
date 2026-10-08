/* SPDX-License-Identifier: GPL-3.0-or-later */
/* A deny-write VFS around SQLite's actual platform locks. WAL is compiled out;
 * we never use immutable=1/nolock=1 on a live database or copy it over FTP. */
#define _POSIX_C_SOURCE 200809L
#include "schema_probe.h"
#include <sqlite3.h>
#include <errno.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
#ifdef PS5_SQLITE_DESCRIPTOR_STAT
#include <fcntl.h>
#include <sys/stat.h>
#include <unistd.h>
/* A read-only compatibility replacement for SQLite's lstat syscall only.
 * Reject symlinks instead of resolving them. No pathname shortcut, no locks
 * disabled, no process-wide API patch. Every component still gets checked. */
static int descriptor_stat(const char *name,struct stat *status) {
    int fd=open(name,O_RDONLY|O_NOFOLLOW|O_CLOEXEC|O_NONBLOCK);
    if (fd<0) return -1;
    int rc=fstat(fd,status);int error=errno;
    if (!rc && !S_ISREG(status->st_mode) && !S_ISDIR(status->st_mode)) { rc=-1;error=EINVAL; }
    close(fd);errno=error;return rc;
}
#endif

typedef struct {
    sqlite3_file public;
    sqlite3_file *raw;
    sqlite3_io_methods methods;
} Guard;
static sqlite3_vfs guarded;
static sqlite3_vfs *original;
static int failure_stage,failure_errno;
static void remember_failure(int stage,int rc) {
    if (rc && !failure_stage) { failure_stage=stage;failure_errno=errno; }
}
static int full_path(sqlite3_vfs *v,const char *name,int n,char *out) {
    (void)v;errno=0;int rc=original->xFullPathname(original,name,n,out);
    remember_failure(1,rc);return rc;
}
static int close_file(sqlite3_file *f) { Guard *g=(Guard*)f; return g->raw->pMethods->xClose(g->raw); }
static int read_file(sqlite3_file *f,void *p,int n,sqlite3_int64 o) { Guard *g=(Guard*)f; return g->raw->pMethods->xRead(g->raw,p,n,o); }
static int write_file(sqlite3_file *f,const void *p,int n,sqlite3_int64 o) { (void)f;(void)p;(void)n;(void)o; return SQLITE_READONLY; }
static int truncate_file(sqlite3_file *f,sqlite3_int64 n) { (void)f;(void)n; return SQLITE_READONLY; }
static int sync_file(sqlite3_file *f,int flags) { (void)f;(void)flags; return SQLITE_READONLY; }
static int size_file(sqlite3_file *f,sqlite3_int64 *n) { Guard *g=(Guard*)f; return g->raw->pMethods->xFileSize(g->raw,n); }
static int lock_file(sqlite3_file *f,int mode) {
    Guard *g=(Guard*)f;errno=0;int rc=g->raw->pMethods->xLock(g->raw,mode);
    remember_failure(3,rc);return rc;
}
static int unlock_file(sqlite3_file *f,int mode) { Guard *g=(Guard*)f; return g->raw->pMethods->xUnlock(g->raw,mode); }
static int check_lock(sqlite3_file *f,int *out) { Guard *g=(Guard*)f; return g->raw->pMethods->xCheckReservedLock(g->raw,out); }
static int control_file(sqlite3_file *f,int op,void *arg) { (void)f;(void)op;(void)arg; return SQLITE_NOTFOUND; }
static int sector_file(sqlite3_file *f) { Guard *g=(Guard*)f; return g->raw->pMethods->xSectorSize(g->raw); }
static int characteristics_file(sqlite3_file *f) { Guard *g=(Guard*)f; return g->raw->pMethods->xDeviceCharacteristics(g->raw); }
static int delete_file(sqlite3_vfs *v,const char *name,int sync) { (void)v;(void)name;(void)sync; return SQLITE_IOERR_DELETE; }
static int open_file(sqlite3_vfs *v,const char *name,sqlite3_file *f,int flags,int *out) {
    (void)v;
    memset(f,0,(size_t)guarded.szOsFile);
    if (!name || !(flags&SQLITE_OPEN_READONLY) || (flags&(SQLITE_OPEN_READWRITE|SQLITE_OPEN_CREATE|SQLITE_OPEN_DELETEONCLOSE)))
        return SQLITE_READONLY;
    Guard *g=(Guard*)f; g->raw=(sqlite3_file*)(g+1);
    errno=0;int rc=original->xOpen(original,name,g->raw,flags,out);
    remember_failure(2,rc);
    if (rc) return rc;
    g->methods=(sqlite3_io_methods){.iVersion=1,.xClose=close_file,.xRead=read_file,.xWrite=write_file,
        .xTruncate=truncate_file,.xSync=sync_file,.xFileSize=size_file,.xLock=lock_file,
        .xUnlock=unlock_file,.xCheckReservedLock=check_lock,.xFileControl=control_file,
        .xSectorSize=sector_file,.xDeviceCharacteristics=characteristics_file};
    g->public.pMethods=&g->methods;
    return SQLITE_OK;
}
static int budget(void *context) {
    struct timespec now;
    if (clock_gettime(CLOCK_MONOTONIC,&now)) return 1;
    return now.tv_sec >= *(time_t*)context;
}

SchemaProbe schema_probe(const char *path) {
    failure_stage=failure_errno=0;
    SchemaProbe result={.rc=SQLITE_ERROR};
    sqlite3 *db=NULL; sqlite3_stmt *statement=NULL;
    if (sqlite3_initialize()) return result;
    if (!original) {
        original=sqlite3_vfs_find(NULL);
        if (!original) return result;
#ifdef PS5_SQLITE_DESCRIPTOR_STAT
        if (!original->xSetSystemCall ||
            original->xSetSystemCall(original,"lstat",(sqlite3_syscall_ptr)descriptor_stat)!=SQLITE_OK)
            return result;
#endif
        guarded=*original;
        guarded.zName="ps5-sync-deny-write"; guarded.szOsFile=original->szOsFile+(int)sizeof(Guard);
        guarded.xOpen=open_file; guarded.xDelete=delete_file;guarded.xFullPathname=full_path;
        if (sqlite3_vfs_register(&guarded,0)) return result;
    }
    int rc=sqlite3_open_v2(path,&db,SQLITE_OPEN_READONLY|SQLITE_OPEN_NOFOLLOW,guarded.zName);
    if (rc) goto finished;
    if (sqlite3_db_readonly(db,"main") != 1) { rc=SQLITE_READONLY; goto finished; }
    sqlite3_busy_timeout(db,250);
    struct timespec start;
    if (clock_gettime(CLOCK_MONOTONIC,&start)) { rc=SQLITE_ERROR; goto finished; }
    time_t deadline=start.tv_sec+3;
    sqlite3_progress_handler(db,100,budget,&deadline);
    sqlite3_limit(db,SQLITE_LIMIT_LENGTH,1024*1024);
    sqlite3_limit(db,SQLITE_LIMIT_SQL_LENGTH,4096);
    sqlite3_db_config(db,SQLITE_DBCONFIG_TRUSTED_SCHEMA,0,NULL);
    sqlite3_db_config(db,SQLITE_DBCONFIG_DEFENSIVE,1,NULL);
    rc=sqlite3_exec(db,"PRAGMA query_only=ON; BEGIN",NULL,NULL,NULL);
    if (rc) goto finished;
    rc=sqlite3_prepare_v2(db,"SELECT name FROM sqlite_schema WHERE type='table' AND name='tbl_log'",-1,&statement,NULL);
    if (rc) goto finished;
    rc=sqlite3_step(statement);
    if (rc==SQLITE_ROW) result.activity_table=1;
    else if (rc!=SQLITE_DONE) goto finished;
    result.read_transaction=1;
    sqlite3_finalize(statement);statement=NULL;
    rc=sqlite3_prepare_v2(db,"PRAGMA journal_mode",-1,&statement,NULL);
    if (rc) goto finished;
    rc=sqlite3_step(statement);
    if (rc!=SQLITE_ROW) goto finished;
    const char *mode=(const char*)sqlite3_column_text(statement,0);
    if (mode && (!strcmp(mode,"delete")||!strcmp(mode,"truncate")||!strcmp(mode,"persist")||!strcmp(mode,"off")||!strcmp(mode,"memory")))
        snprintf(result.journal_mode,sizeof(result.journal_mode),"%s",mode);
    sqlite3_finalize(statement);statement=NULL;
    rc=sqlite3_prepare_v2(db,"SELECT name FROM pragma_table_info('tbl_log')",-1,&statement,NULL);
    if (rc) goto finished;
    while ((rc=sqlite3_step(statement))==SQLITE_ROW) {
        const char *column=(const char*)sqlite3_column_text(statement,0);
        if (column && !strcmp(column,"created_date")) result.created_date_column=1;
        if (column && !strcmp(column,"log")) result.log_column=1;
        if (column && !strcmp(column,"event_id")) result.event_id_column=1;
    }
    if (rc==SQLITE_DONE) rc=SQLITE_OK;
#ifdef PS5_ACTIVITY_SHAPE_PROBE
    sqlite3_finalize(statement);statement=NULL;
    result.shape_rc=SQLITE_NOTFOUND;
    if (!rc && result.event_id_column) {
        int shape=sqlite3_prepare_v2(db,"SELECT typeof(created_date),json_valid(log) FROM (SELECT created_date,log FROM tbl_log WHERE event_id='ApplicationSessionEndBi' AND length(log)<=65536 LIMIT 32)",-1,&statement,NULL);
        if (!shape) while ((shape=sqlite3_step(statement))==SQLITE_ROW) {
            const char *type=(const char*)sqlite3_column_text(statement,0);
            result.shape_rows++;result.json_rows+=sqlite3_column_int(statement,1)!=0;
            if(type && !strcmp(type,"integer")) result.date_type_mask|=1;
            else if(type && !strcmp(type,"text")) result.date_type_mask|=2;
            else result.date_type_mask|=4;
        }
        sqlite3_finalize(statement);statement=NULL;
        if (shape==SQLITE_DONE) shape=SQLITE_OK;
        if (!shape) {
            static const char *keys[]={"totalFgTime","titleId","userId","localUserId","sessionId","applicationId","startTime","endTime","duration","foregroundTime","accountId","contentId","sessionStartTime","sessionEndTime","totalSessionTime","sessionFgTime","appTitleId","psnAccountId","uid","localUser","user_id","account_id","startTimeStamp","endTimeStamp","sessionGuid","sessionUuid","appSessionId","totalTime","userIdx","profileId"};
            shape=sqlite3_prepare_v2(db,"SELECT DISTINCT j.key FROM (SELECT log FROM tbl_log WHERE event_id='ApplicationSessionEndBi' AND length(log)<=65536 LIMIT 32) s,json_tree(CASE WHEN json_valid(s.log) THEN s.log ELSE '{}' END) j WHERE j.key IS NOT NULL LIMIT 512",-1,&statement,NULL);
            if (!shape) while ((shape=sqlite3_step(statement))==SQLITE_ROW) {
                const char *key=(const char*)sqlite3_column_text(statement,0);
                if (key) for (unsigned i=0;i<sizeof(keys)/sizeof(keys[0]);i++)
                    if (!strcmp(key,keys[i])) result.shape_key_mask|=1u<<i;
            }
            sqlite3_finalize(statement);statement=NULL;
            if (shape==SQLITE_DONE) shape=SQLITE_OK;
        }
#ifdef PS5_ACTIVITY_TYPE_PROBE
        if (!shape) {
            shape=sqlite3_prepare_v2(db,
                "SELECT json_type(log,'$.appTitleId'),json_extract(log,'$.appTitleId') GLOB 'PPSA[0-9][0-9][0-9][0-9][0-9]',"
                "json_type(log,'$.totalFgTime'),json_extract(log,'$.totalFgTime')>=0,julianday(created_date) IS NOT NULL "
                "FROM (SELECT created_date,CASE WHEN json_valid(log) THEN log ELSE '{}' END log FROM tbl_log "
                "WHERE event_id='ApplicationSessionEndBi' AND length(log)<=65536 LIMIT 32)",-1,&statement,NULL);
            if (!shape) while ((shape=sqlite3_step(statement))==SQLITE_ROW) {
                const char *title_type=(const char*)sqlite3_column_text(statement,0);
                const char *fg_type=(const char*)sqlite3_column_text(statement,2);
                if(title_type && !strcmp(title_type,"text") && sqlite3_column_int(statement,1)) result.app_title_rows++;
                if(fg_type && (!strcmp(fg_type,"integer")||!strcmp(fg_type,"real")) && sqlite3_column_int(statement,3)) result.foreground_numeric_rows++;
                result.date_parseable_rows+=sqlite3_column_int(statement,4)!=0;
            }
            sqlite3_finalize(statement);statement=NULL;
            if (shape==SQLITE_DONE) shape=SQLITE_OK;
        }
#endif
        result.shape_rc=shape;
    }
#endif
finished:
    if (statement) sqlite3_finalize(statement);
    if (db) { sqlite3_exec(db,"ROLLBACK",NULL,NULL,NULL); sqlite3_close(db); }
    result.rc=rc;
    result.failure_stage=failure_stage;result.failure_errno=failure_errno;
    return result;
}
