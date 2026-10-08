/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once
#include <stddef.h>
/* App-owned private directory only. Fixed leaf names, no symlinks, exclusive
 * private temporary file, atomic rename and fsync. Never a system database. */
int state_open(const char *directory);
int state_read(int dir,const char *name,void *bytes,size_t size);
int state_write(int dir,const char *name,const void *bytes,size_t size);
/* Non-secret failure evidence from the single pairing worker. */
const char *state_error_operation(void);
int state_error_code(void);
const char *state_identity_evidence(void);
void state_set_progress(void (*progress)(unsigned stage));
