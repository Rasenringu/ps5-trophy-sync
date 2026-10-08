/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once
typedef struct {
    int rc;
    int read_transaction;
    int activity_table;
    int created_date_column;
    int log_column;
    char journal_mode[16];
    int failure_stage; /* 1 full path, 2 open, 3 lock; 0 means no VFS failure. */
    int failure_errno;
    int event_id_column;
    int shape_rc,shape_rows,json_rows,date_type_mask;
    unsigned shape_key_mask;
    int app_title_rows,foreground_numeric_rows,date_parseable_rows;
} SchemaProbe;
/* Only SQLite metadata. No activity rows, writes, copies or WAL support. */
SchemaProbe schema_probe(const char *path);
