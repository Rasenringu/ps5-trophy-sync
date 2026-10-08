/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once
#include <stddef.h>
#define SYNC_QUEUE_SLOTS 64
typedef struct {
    char magic[8];unsigned version,acknowledged,profile,length;
    char installation[37],profile_uuid[37],origin[192];
    unsigned char digest[32];char json[8193];
} SyncQueueItem;
/* All writes use validated private state and fsync/rename/directory-fsync.
 * Slots are reused only after a durable acknowledgement, never on HTTP failure.
 * Exact installation/profile/origin scope; no credential fields. */
int sync_queue_load(int directory,unsigned profile,unsigned slot,const char *installation,
                    const char *profile_uuid,const char *origin,SyncQueueItem *item);
int sync_queue_put(int directory,unsigned profile,const char *installation,
                   const char *profile_uuid,const char *origin,const char *json,unsigned *slot);
int sync_queue_ack(int directory,unsigned slot,SyncQueueItem *item);
