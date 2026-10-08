/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Actual native UCP captures: schemas0.90/1.00 config + localized metadata. */
#define _POSIX_C_SOURCE 200809L
#include "native_definitions.h"
#include <sqlite3.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
static int budget(void *context) {
    struct timespec now;
    return clock_gettime(CLOCK_MONOTONIC,&now) || now.tv_sec>=*(time_t*)context;
}
static int text(sqlite3_stmt *s,int column,char *target,size_t capacity,unsigned max_chars) {
    const unsigned char *p=sqlite3_column_text(s,column);int length=sqlite3_column_bytes(s,column);
    if(!p || length<1 || (size_t)length>=capacity || memchr(p,0,(size_t)length)) return 0;
    /* Strict UTF8: avoid invalid Unicode or counting bytes as characters. */
    unsigned chars=0;size_t offset=0;
    while(offset<(size_t)length) {
        unsigned first=p[offset++],cp=first,width=1,min=0;
        if(first>=0xc2 && first<=0xdf) { width=2;cp=first&31;min=0x80; }
        else if(first>=0xe0 && first<=0xef) { width=3;cp=first&15;min=0x800; }
        else if(first>=0xf0 && first<=0xf4) { width=4;cp=first&7;min=0x10000; }
        else if(first>=0x80) return 0;
        if(offset+width-1>(size_t)length) return 0;
        for(unsigned i=1;i<width;i++) { unsigned x=p[offset++];if((x&0xc0)!=0x80) return 0;cp=(cp<<6)|(x&63); }
        if(cp<min || cp>0x10ffff || (cp>=0xd800 && cp<=0xdfff) || ++chars>max_chars) return 0;
    }
    memcpy(target,p,(size_t)length);target[length]=0;return 1;
}
static int query(sqlite3 *db,const char *sql,const UcpEntry *a,const UcpEntry *b,sqlite3_stmt **s) {
    int rc=sqlite3_prepare_v2(db,sql,-1,s,NULL);
    if(!rc) rc=sqlite3_bind_text(*s,1,(const char*)a->bytes,(int)a->size,SQLITE_STATIC);
    if(!rc && b) rc=sqlite3_bind_text(*s,2,(const char*)b->bytes,(int)b->size,SQLITE_STATIC);
    return rc;
}
static int valid_json(sqlite3 *db,const UcpEntry *entry) {
    if(!entry->size || entry->size>1024*1024) return 0;
    sqlite3_stmt *s=NULL;int ok=0;
    if(!query(db,"SELECT json_valid(?1)",entry,NULL,&s) && sqlite3_step(s)==SQLITE_ROW) ok=sqlite3_column_int(s,0)==1;
    sqlite3_finalize(s);s=NULL;if(!ok) return 0;
    /* Duplicate object keys must not silently select an arbitrary definition. */
    ok=!query(db,"SELECT 1 FROM json_tree(?1) GROUP BY fullkey HAVING count(*)>1 LIMIT 1",entry,NULL,&s) && sqlite3_step(s)==SQLITE_DONE;
    sqlite3_finalize(s);return ok;
}
void native_definitions_free(NativeDefinitions *result) {
    if(result) { free(result->trophies);memset(result,0,sizeof(*result)); }
}
int native_definitions(const Ucp *archive,NativeDefinitions *result) {
    if(!result) return 1;
    memset(result,0,sizeof(*result));UcpEntry conf,metadata;
    if(ucp_find(archive,"tropconf.json",&conf)) return 1;
    sqlite3 *db=NULL;sqlite3_stmt *s=NULL;int rc=1;
    /* Dedicated in-memory JSON interpreter. No console/source database opens. */
    if(sqlite3_open_v2(":memory:",&db,SQLITE_OPEN_READWRITE|SQLITE_OPEN_CREATE|SQLITE_OPEN_NOMUTEX,NULL)!=SQLITE_OK) goto done;
    sqlite3_limit(db,SQLITE_LIMIT_LENGTH,1024*1024);
    sqlite3_db_config(db,SQLITE_DBCONFIG_TRUSTED_SCHEMA,0,NULL);
    sqlite3_db_config(db,SQLITE_DBCONFIG_DEFENSIVE,1,NULL);
    struct timespec start;
    if(clock_gettime(CLOCK_MONOTONIC,&start)) goto done;
    time_t deadline=start.tv_sec+3;sqlite3_progress_handler(db,100,budget,&deadline);
    if(!valid_json(db,&conf)) goto done;
    if(query(db,"SELECT json_extract(?1,'$.schemaVersion'),json_extract(?1,'$.trophyNpCommId'),json_extract(?1,'$.defaultLanguage'),json_type(?1,'$.trophies'),json_array_length(?1,'$.trophies'),json_type(?1,'$.platform')='array' AND EXISTS(SELECT 1 FROM json_each(?1,'$.platform') WHERE value='PS5')",&conf,NULL,&s) || sqlite3_step(s)!=SQLITE_ROW) goto done;
    const char *schema=(const char*)sqlite3_column_text(s,0),*kind=(const char*)sqlite3_column_text(s,3);
    int count=sqlite3_column_int(s,4);
    if(!schema || (strcmp(schema,"0.90")&&strcmp(schema,"1.00")) || !kind || strcmp(kind,"array") || count<1 || count>1000 || !sqlite3_column_int(s,5)) goto done;
    if(!text(s,1,result->npwr,sizeof(result->npwr),12) || strlen(result->npwr)!=12 || strncmp(result->npwr,"NPWR",4) || strcmp(result->npwr+9,"_00")) goto done;
    for(unsigned i=4;i<9;i++) if(result->npwr[i]<'0' || result->npwr[i]>'9') goto done;
    if(!text(s,2,result->language,sizeof(result->language),15)) goto done;
    for(const char *p=result->language;*p;p++) if(!((*p>='a'&&*p<='z')||(*p>='A'&&*p<='Z')||(*p>='0'&&*p<='9')||*p=='-')) goto done;
    sqlite3_finalize(s);s=NULL;
    char filename[64];snprintf(filename,sizeof(filename),"tropmeta_%s.json",result->language);
    if(ucp_find(archive,filename,&metadata) || !valid_json(db,&metadata)) goto done;
    if(query(db,"SELECT json_extract(?2,'$.metadata.titleMetadata.name'),json_type(?2,'$.metadata.titleMetadata.name')='text' AND json_extract(?2,'$.schemaVersion')='0.90',json_extract(?2,'$.trophyNpCommId')=json_extract(?1,'$.trophyNpCommId'),json_extract(?2,'$.trophyDefinitionRevision')=json_extract(?1,'$.trophyDefinitionRevision'),json_extract(?2,'$.trophySetVersion')=json_extract(?1,'$.trophySetVersion'),json_type(?2,'$.metadata.trophyMetadata'),json_array_length(?2,'$.metadata.trophyMetadata')",&conf,&metadata,&s) || sqlite3_step(s)!=SQLITE_ROW) goto done;
    if(!text(s,0,result->title,sizeof(result->title),200)) goto done;
    for(int i=1;i<=4;i++) if(sqlite3_column_int(s,i)!=1) goto done;
    kind=(const char*)sqlite3_column_text(s,5);
    if(!kind || strcmp(kind,"array") || sqlite3_column_int(s,6)!=count) goto done;
    sqlite3_finalize(s);s=NULL;
    result->trophies=calloc((size_t)count,sizeof(*result->trophies));if(!result->trophies) goto done;
    if(query(db,"SELECT json_extract(c.value,'$.id'),json_extract(c.value,'$.grade'),json_type(c.value,'$.hidden'),json_extract(m.value,'$.name') FROM json_each(?1,'$.trophies') c JOIN json_each(?2,'$.metadata.trophyMetadata') m ON json_extract(c.value,'$.id')=json_extract(m.value,'$.id') WHERE json_type(c.value,'$.id')='text' AND json_type(c.value,'$.grade')='text' AND json_type(m.value,'$.id')='text' AND json_type(m.value,'$.name')='text'",&conf,&metadata,&s)) goto done;
    int step;
    while((step=sqlite3_step(s))==SQLITE_ROW) {
        if(result->count>=(unsigned)count) goto done;
        NativeDefinition *t=&result->trophies[result->count];char grade[8],hidden[8];
        if(!text(s,0,t->id,sizeof(t->id),64) || !text(s,1,grade,sizeof(grade),1) || !strchr("BSGP",grade[0]) || !text(s,2,hidden,sizeof(hidden),5) || (strcmp(hidden,"true")&&strcmp(hidden,"false")) || !text(s,3,t->name,sizeof(t->name),200)) goto done;
        for(unsigned i=0;i<result->count;i++) if(!strcmp(result->trophies[i].id,t->id)) goto done;
        t->grade=grade[0];t->hidden=!strcmp(hidden,"true");result->count++;
    }
    if(step!=SQLITE_DONE || result->count!=(unsigned)count) goto done;
    rc=0;
done:
    sqlite3_finalize(s);if(db) sqlite3_close(db);
    if(rc) native_definitions_free(result);
    return rc;
}
