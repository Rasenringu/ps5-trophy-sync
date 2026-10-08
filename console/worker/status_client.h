/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once
#include "status.h"
/* Connector evidence only, no credentials or profile values. */
unsigned worker_connect_stage(void);
int worker_connect_errno(void);
