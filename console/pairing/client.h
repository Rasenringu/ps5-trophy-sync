/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once
#include "../ui/screen.h"
typedef struct {
    char installation_id[37],installation_secret[129],device_code[129],device_token[129],profile_uuid[37];
    char origin[192];unsigned profile;int directory;unsigned attempts;
    unsigned long long next_poll_ms,deadline_ms;
} PairClient;
int pair_start(PairClient *c,UiModel *ui,unsigned profile,unsigned long long now);
void pair_tick(PairClient *c,UiModel *ui,unsigned long long now);
/* Optional single-worker fixed-stage diagnostic; contains no credentials. */
void pair_set_progress(void (*progress)(unsigned stage));
