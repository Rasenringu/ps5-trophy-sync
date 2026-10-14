/* SPDX-License-Identifier: GPL-3.0-or-later */
/* One-shot investigation: locked read-only SQLite queries, redacted report only.
 * No trophy mounting, source writes, network imports or credential reads. */
#include "../readers/native_activity.h"
#include "../readers/schema_probe.h"
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>
int __patch_init(void){return 0;}
extern int sceUserServiceInitialize(void*);
extern int sceUserServiceGetForegroundUser(uint32_t*);
static uint32_t selected;
static int same_user(void){uint32_t user=UINT32_MAX;return !sceUserServiceGetForegroundUser(&user)&&user==selected;}
static void schema(FILE *report,const char *path,const char *label){
    SchemaProbe probe=schema_probe(path);
    fprintf(report,"%s: rc=%d journal=%s\n",label,probe.rc,probe.journal_mode);
    if(probe.rc||strcmp(probe.journal_mode,"delete")||!same_user())return;
    sqlite3 *db=NULL;sqlite3_stmt *q=NULL;
    if(sqlite3_open_v2(path,&db,SQLITE_OPEN_READONLY|SQLITE_OPEN_NOFOLLOW,"ps5-sync-deny-write"))goto done;
    sqlite3_busy_timeout(db,250);sqlite3_db_config(db,SQLITE_DBCONFIG_TRUSTED_SCHEMA,0,NULL);
    if(sqlite3_exec(db,"PRAGMA query_only=ON; BEGIN",NULL,NULL,NULL))goto done;
    if(sqlite3_prepare_v2(db,"SELECT name FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%' LIMIT 32",-1,&q,NULL))goto done;
    while(sqlite3_step(q)==SQLITE_ROW&&same_user()){
        const char *name=(const char*)sqlite3_column_text(q,0);if(!name)continue;
        const char *suffix=strrchr(name,'_');
        if(suffix&&suffix[1]&&strspn(suffix+1,"0123456789")==strlen(suffix+1))
            fprintf(report,"table=%.*s_<profile>\n",(int)(suffix-name),name);
        else fprintf(report,"table=%s\n",name);
        sqlite3_stmt *columns=NULL;
        if(!sqlite3_prepare_v2(db,"SELECT name,type FROM pragma_table_info(?1) LIMIT 64",-1,&columns,NULL)){
            sqlite3_bind_text(columns,1,name,-1,SQLITE_TRANSIENT);
            while(sqlite3_step(columns)==SQLITE_ROW&&same_user())fprintf(report,"column=%s type=%s\n",sqlite3_column_text(columns,0),sqlite3_column_text(columns,1));
        }
        sqlite3_finalize(columns);
    }
done:sqlite3_finalize(q);if(db){sqlite3_exec(db,"ROLLBACK",NULL,NULL,NULL);sqlite3_close(db);}
}
int main(void){
    if(geteuid()!=0||sceUserServiceInitialize(NULL)||sceUserServiceGetForegroundUser(&selected)||selected==UINT32_MAX)return 1;
    const char *path="/data/trophy-sync-library-report.txt";
    int fd=open(path,O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC,0600);
    if(fd<0)return 2;struct stat st;
    if(fstat(fd,&st)||!S_ISREG(st.st_mode)||st.st_uid!=geteuid()||(st.st_mode&077)!=0){close(fd);return 3;}
    FILE *report=fdopen(fd,"w");if(!report){close(fd);return 4;}
    fprintf(report,"TrophySync read-only library diagnostic v1\nNo profile identifiers, session IDs, credentials or raw logs exported.\n");
    sqlite3 *memory=NULL;NativeActivityCounts counts;
    int rc=native_activity_collect("/system_data/priv/system_logger2/nobackup/database/sl2_log.db",selected,&memory,&counts);
    fprintf(report,"activity: rc=%d rows=%u sessions=%u complete=%u incomplete=%u rejected=%u\n",rc,counts.rows,counts.sessions,counts.completed,counts.incomplete,counts.rejected);
    if(!rc&&same_user()){
        sqlite3_stmt *q=NULL;
        if(!sqlite3_prepare_v2(memory,"SELECT title_id,title,count(*),sum(seconds IS NOT NULL),sum(seconds) FROM sessions GROUP BY title_id,title",-1,&q,NULL))
            while(sqlite3_step(q)==SQLITE_ROW&&same_user())
                fprintf(report,"title=%s name=%s sessions=%d completed=%d recorded_seconds=%lld\n",sqlite3_column_text(q,0),sqlite3_column_text(q,1),sqlite3_column_int(q,2),sqlite3_column_int(q,3),(long long)sqlite3_column_int64(q,4));
        sqlite3_finalize(q);
    }
    sqlite3_close(memory);
    schema(report,"/system_data/priv/mms/app.db","application metadata");
    schema(report,"/system_data/priv/mms/appinfo.db","application info metadata");
    char source[256];snprintf(source,sizeof(source),"/user/home/%08x/trophy/db/trophy_local.db",selected);
    schema(report,source,"PS4 profile trophy db");
    snprintf(source,sizeof(source),"/mnt/pfs/trophy/%08x/db/trophy_local.db",selected);
    schema(report,source,"PS4 mounted trophy db");
    int ok=same_user()&&!ferror(report)&&!fflush(report)&&!fsync(fd);
    fclose(report);return ok?0:5;
}
