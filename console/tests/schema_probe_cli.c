/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "../readers/schema_probe.h"
#include <stdio.h>
int main(int argc,char **argv) {
    if (argc!=2) return 2;
    SchemaProbe r=schema_probe(argv[1]);
    printf("%d %d %d %d %d %s\n",r.rc,r.read_transaction,r.activity_table,
        r.created_date_column,r.log_column,r.journal_mode[0] ? r.journal_mode : "unknown");
    return 0;
}
