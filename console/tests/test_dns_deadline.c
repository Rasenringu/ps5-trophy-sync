/* SPDX-License-Identifier: GPL-3.0-or-later */
#define _GNU_SOURCE 1
#include <assert.h>
#include <arpa/inet.h>
#include <errno.h>
#include <fcntl.h>
#include <netdb.h>
#include <netinet/in.h>
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
static int stalled_resolver(const char *host,const char *service,
                            const struct addrinfo *hints,struct addrinfo **answers) {
    (void)host;(void)service;(void)hints;*answers=NULL;
    usleep(4000000);return EAI_NONAME;
}
#define getaddrinfo stalled_resolver
#include "../transport/https_io.h"
int main(void) {
    HttpsResult result={0};int64_t start=monotonic_ms();
    assert(connect_bounded("MOCK-stalled.invalid",443,&result)==-1);
    assert(result.posix_errno==ETIMEDOUT);
    assert(monotonic_ms()-start>=3000&&monotonic_ms()-start<3500);
    start=monotonic_ms();
    assert(connect_bounded("MOCK-stalled.invalid",443,&result)==-1);
    assert(result.posix_errno==EAGAIN&&monotonic_ms()-start<100);
    usleep(1500000);
    pthread_mutex_lock(&dns.mutex);
    assert(dns.active&&dns.done&&dns.count==0);
    pthread_mutex_unlock(&dns.mutex);
    puts("PASS MOCK DNS: stalled resolver bounded to 3s; retry creates no extra thread; late completion safely retained.");
}
