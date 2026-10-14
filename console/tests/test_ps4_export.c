/* SPDX-License-Identifier: GPL-3.0-or-later */
/* MOCK state; verify bounded upload, unknown-state preservation and raw times. */
#include "../sync/ps4_export.h"
#include <assert.h>
#include <limits.h>
#include <stdio.h>
#include <string.h>
int main(void){
    Ps4StateRecord rows[3]={{.id=0,.grade=4,.unlocked=0},
        {.id=1,.grade=3,.raw_state=1,.raw_aux=0x2000,.first_raw=63800000000000001ULL,.second_raw=UINT64_MAX,.unlocked=1},
        {.id=2,.grade=2,.raw_state=99,.unlocked=-1}};
    Ps4State s={.title="NPWR00001_00",.applications={"CUSA00001"},.application_count=1,.count=3,.records=rows};
    sqlite3 *db=NULL;char json[8193];const char *uuid="00000000-0000-4000-8000-000000000001";
    assert(!ps4_export_prepare(&s,&db));assert(!ps4_export_batch(db,uuid,0,3,json));
    assert(strstr(json,"\"schema_version\":4")&&strstr(json,"\"unlocked\":null"));
    assert(strstr(json,"18446744073709551615")&&strstr(json,"\"clock\":\"uncertain\""));
    assert(strstr(json,".000001Z")&&strstr(json,"CUSA00001"));
    assert(!strstr(json,"account")&&!strstr(json,"sealedkey")&&!strstr(json,"local_user_id"));
    assert(ps4_export_batch(db,uuid,UINT_MAX,3,json)<0);
    assert(ps4_export_batch(db,uuid,0,4,json)<0);sqlite3_close(db);
    s.application_count=17;assert(ps4_export_prepare(&s,&db)<0&&!db);s.application_count=1;
    strcpy(s.applications[0],"CUSA00\"01");assert(ps4_export_prepare(&s,&db)<0);strcpy(s.applications[0],"CUSA00001");
    rows[0].grade=5;assert(ps4_export_prepare(&s,&db)<0);rows[0].grade=4;
    rows[2].unlocked=0;assert(ps4_export_prepare(&s,&db)<0);
    puts("PASS MOCK PS4 export: unknown flags, raw uint64, uncertain timestamp, upload privacy and range overflow");
    return 0;
}
