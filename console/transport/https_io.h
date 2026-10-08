/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once
#include <netdb.h>
#include <pthread.h>

/* One outstanding resolver per transport. A stalled system resolver cannot
 * block the worker or accumulate threads on repeated retries. DNS is never
 * trusted as identity: TLS still verifies the configured service hostname. */
static struct {
    pthread_mutex_t mutex;
    int active, done, count;
    char host[193];
    struct in_addr addresses[8];
} dns = {.mutex=PTHREAD_MUTEX_INITIALIZER};
static void *resolve_host(void *unused) {
    (void)unused;
    struct addrinfo hints={.ai_family=AF_INET,.ai_socktype=SOCK_STREAM}, *answers=NULL;
    struct in_addr addresses[8];int count=0;
    if(!getaddrinfo(dns.host,NULL,&hints,&answers)) {
        for(struct addrinfo *a=answers;a&&count<8;a=a->ai_next)
            if(a->ai_family==AF_INET&&a->ai_addrlen>=sizeof(struct sockaddr_in))
                addresses[count++]=((struct sockaddr_in*)a->ai_addr)->sin_addr;
        freeaddrinfo(answers);
    }
    pthread_mutex_lock(&dns.mutex);
    memcpy(dns.addresses,addresses,(size_t)count*sizeof(*addresses));
    dns.count=count;dns.done=1;
    pthread_mutex_unlock(&dns.mutex);
    return NULL;
}
typedef struct { int fd; int64_t deadline; } Connection;
static int64_t monotonic_ms(void) {
    struct timespec ts;
    if (clock_gettime(CLOCK_MONOTONIC, &ts)) return -1;
    return (int64_t)ts.tv_sec*1000 + ts.tv_nsec/1000000;
}

/* Keep sockets nonblocking for their entire lifetime. A timeout option on a
 * blocking connect is not a safe substitute on the BSD connect path. */
static int wait_io(Connection *c,int writing) {
    int64_t now=monotonic_ms();
    if (now<0 || now>=c->deadline) return MBEDTLS_ERR_SSL_TIMEOUT;
    int64_t remaining=c->deadline-now;
    if (remaining>3000) remaining=3000;
    struct timeval timeout={remaining/1000,(remaining%1000)*1000};
    fd_set ready;FD_ZERO(&ready);FD_SET(c->fd,&ready);
    int rc=select(c->fd+1,writing ? NULL : &ready,writing ? &ready : NULL,NULL,&timeout);
    if (!rc) return MBEDTLS_ERR_SSL_TIMEOUT;
    if (rc<0) return errno==EINTR ? (writing ? MBEDTLS_ERR_SSL_WANT_WRITE : MBEDTLS_ERR_SSL_WANT_READ) : MBEDTLS_ERR_NET_POLL_FAILED;
    return 0;
}
static int transmit(void *context, const unsigned char *data, size_t size) {
    Connection *c=context;
    int rc=wait_io(c,1);if (rc) return rc;
    ssize_t n=send(c->fd,data,size,0);
    if (n>=0) return (int)n;
    if (errno==EAGAIN || errno==EWOULDBLOCK || errno==EINTR) return MBEDTLS_ERR_SSL_WANT_WRITE;
    return MBEDTLS_ERR_NET_SEND_FAILED;
}
static int receive(void *context, unsigned char *data, size_t size) {
    Connection *c=context;
    int rc=wait_io(c,0);if (rc) return rc;
    ssize_t n=recv(c->fd,data,size,0);
    if (n>=0) return (int)n;
    if (errno==EAGAIN || errno==EWOULDBLOCK || errno==EINTR) return MBEDTLS_ERR_SSL_WANT_READ;
    return MBEDTLS_ERR_NET_RECV_FAILED;
}
static int connect_address(struct in_addr ip, uint16_t port, HttpsResult *result) {
    struct sockaddr_in address;
    memset(&address, 0, sizeof(address));
#if defined(__FreeBSD__)
    address.sin_len = sizeof(address);
#endif
    address.sin_family = AF_INET;
    address.sin_port = htons(port);
    result->connect_stage=1;
    address.sin_addr=ip;
    result->connect_stage=2;
    int fd = socket(AF_INET, SOCK_STREAM|SOCK_NONBLOCK, 0);
    if (fd < 0) { result->posix_errno=errno; return -1; }
    result->connect_stage=3;
    if (fd >= FD_SETSIZE) { errno=EMFILE;goto failed; }
    result->connect_stage=4;
    int flags=fcntl(fd,F_GETFL,0);
    if (flags<0) goto failed;
    if (!(flags&O_NONBLOCK)) { errno=EOPNOTSUPP;goto failed; }
    result->connect_stage=6;
    if (connect(fd, (struct sockaddr*)&address, sizeof(address)) < 0) {
        if (errno != EINPROGRESS) goto failed;
        result->connect_stage=7;
        fd_set writable; FD_ZERO(&writable); FD_SET(fd, &writable);
        struct timeval timeout = {5, 0};
        int ready=select(fd+1, NULL, &writable, NULL, &timeout);
        if (ready != 1) { if (!ready) errno=ETIMEDOUT;goto failed; }
        result->connect_stage=8;
        int error = 0; socklen_t len = sizeof(error);
        if (getsockopt(fd, SOL_SOCKET, SO_ERROR, &error, &len) < 0) goto failed;
        if (error) { result->posix_errno=error;close(fd);return -1; }
    }
    result->connect_stage=12;
    return fd;
failed:
    result->posix_errno=errno;
    close(fd); return -1;
}
static int connect_bounded(const char *host, uint16_t port, HttpsResult *result) {
    struct in_addr addresses[8];int count=0;
    if(inet_pton(AF_INET,host,&addresses[0])==1)count=1;
    else {
        result->connect_stage=1;
        pthread_mutex_lock(&dns.mutex);
        if(dns.active&&!dns.done){pthread_mutex_unlock(&dns.mutex);result->posix_errno=EAGAIN;return -1;}
        dns.active=1;dns.done=0;dns.count=0;
        snprintf(dns.host,sizeof(dns.host),"%s",host);
        pthread_t thread;pthread_attr_t attr;
        int rc=pthread_attr_init(&attr);
        if(!rc){
            rc=pthread_attr_setdetachstate(&attr,PTHREAD_CREATE_DETACHED);
            if(!rc)rc=pthread_create(&thread,&attr,resolve_host,NULL);
            pthread_attr_destroy(&attr);
        }
        if(rc){dns.active=0;pthread_mutex_unlock(&dns.mutex);result->posix_errno=rc;return -1;}
        pthread_mutex_unlock(&dns.mutex);
        int64_t start=monotonic_ms();
        for(;;){
            pthread_mutex_lock(&dns.mutex);
            if(dns.done){
                count=dns.count;memcpy(addresses,dns.addresses,(size_t)count*sizeof(*addresses));dns.active=0;
                pthread_mutex_unlock(&dns.mutex);break;
            }
            pthread_mutex_unlock(&dns.mutex);
            int64_t now=monotonic_ms();
            if(start<0||now<0||now-start>=3000){result->posix_errno=ETIMEDOUT;return -1;}
            usleep(10000);
        }
    }
    if(!count){result->posix_errno=EHOSTUNREACH;return -1;}
    /* Two addresses at most: total DNS + TCP budget is at most 13 seconds. */
    for(int n=0;n<count&&n<2;n++){
        int fd=connect_address(addresses[n],port,result);if(fd>=0)return fd;
    }
    return -1;
}
