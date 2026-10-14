/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once
#include <stddef.h>
/* Source is opened read-only and shared-locked. Destination must be an existing
 * exclusive private regular file. Compare a second complete pass before success.
 * This captures an encrypted PFS container, never an exposed live SQLite DB. */
int ps4_image_snapshot(int source, int destination, size_t limit);
