/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "../ui/screen.h"
#include <assert.h>
#include <string.h>
#include <stdio.h>
int main(void) {
    UiModel m = {0}; char url[256];
    assert(ui_set_pairing(&m, "https://sync.example:443", "ABCD-2345", 1000, 600));
    assert(ui_pairing_link(&m, 1001, url, sizeof(url)));
    assert(!strcmp(url, "https://sync.example:443/pair?code=ABCD-2345"));
    assert(ui_pairing_link(&m, 600999, url, sizeof(url)));
    assert(!ui_pairing_link(&m, 601000, url, sizeof(url)) && !url[0]);
    assert(!ui_pairing_link(&m, 1001, url, 4) && !url[0]);
    const char *bad[] = {"http://sync.example", "https://user:secret@sync.example", "https://sync.example/pair?token=secret", "https://sync.example#secret", "https://sync.example:999999", "https://:443", "https://sync.example:abc", "https://sync.example:0"};
    for (unsigned i = 0; i < sizeof(bad)/sizeof(*bad); i++) {
        assert(!ui_set_pairing(&m, bad[i], "ABCD-2345", 0, 600));
        assert(!ui_pairing_link(&m, 0, url, sizeof(url)));
    }
    assert(!ui_set_pairing(&m, "https://sync.example", "permanent-token", 0, 600));
    assert(!ui_set_pairing(&m, "https://sync.example", "ABCD-2345", 0, 601));
    assert(!ui_set_pairing(&m, "https://sync.example", "ABCD-2345", UINT64_MAX, 1));
    assert(ui_set_pairing(&m, "https://sync.example", "ABCD-2345", 0, 1));
    m.phase = UI_CONNECTED;
    assert(!ui_pairing_link(&m, 0, url, sizeof(url)));
    m.phase = UI_PAIRING;
    memcpy(m.manual_code, "x?token=x", 10);
    assert(!ui_pairing_link(&m, 0, url, sizeof(url)));
    puts("PASS: expiry, stale-code clearing, bounded TTL, origin and secret rejection");
}
