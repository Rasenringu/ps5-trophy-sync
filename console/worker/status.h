/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once
#include <stddef.h>
#include "../ui/screen.h"
#define WORKER_STATUS_PORT 9035
#define WORKER_LOOPBACK_ADDRESS 0x7f000001u
typedef struct {char magic[8];unsigned profile,reserved;} WorkerRequest;
typedef struct {char magic[8];unsigned version,profile,ttl_seconds,reserved;UiModel model;} WorkerStatus;
/* Console loopback status only, no device/installation secrets. Not hardware
 * authentication: another privileged console process remains outside the model. */
int worker_status_valid(const WorkerStatus*,unsigned profile,const char *expected_origin);
int worker_status_fetch(unsigned profile,WorkerStatus*);
int worker_loopback_connect(unsigned short port);
int worker_transfer(int fd,void *bytes,size_t size,int sending);
