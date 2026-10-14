/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Synthetic socket pair. No console, public endpoint or credentials. */
#define _GNU_SOURCE 1
#include <assert.h>
#include <arpa/inet.h>
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/select.h>
#include <sys/socket.h>
#include <time.h>
#include <unistd.h>
#include <mbedtls/net_sockets.h>
#include <mbedtls/ssl.h>
#include "../transport/https_result.h"
#include "../transport/https_io.h"
int main(void){
    int sockets[2];assert(!socketpair(AF_UNIX,SOCK_STREAM,0,sockets));
    int64_t start=monotonic_ms();Connection connection={.fd=sockets[0],.deadline=start+3400};
    assert(wait_io(&connection,0)==MBEDTLS_ERR_SSL_WANT_READ);
    assert(monotonic_ms()-start>=2900&&monotonic_ms()-start<3400);
    assert(wait_io(&connection,0)==MBEDTLS_ERR_SSL_TIMEOUT);
    assert(monotonic_ms()-start>=3400&&monotonic_ms()-start<4000);
    close(sockets[0]);close(sockets[1]);
    puts("PASS MOCK I/O: idle poll slice retries, actual overall deadline still fails closed.");return 0;
}
