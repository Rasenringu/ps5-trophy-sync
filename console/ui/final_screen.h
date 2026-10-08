/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once
#include "screen.h"
/* Same credential-free UiModel/IPC as the installed worker. */
void ui_render_final(uint32_t *pixels,const UiModel *model,uint64_t now_ms);
