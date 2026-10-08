/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once
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
static int connect_bounded(const char *ip, uint16_t port, HttpsResult *result) {
    struct sockaddr_in address;
    memset(&address, 0, sizeof(address));
#if defined(__FreeBSD__)
    address.sin_len = sizeof(address);
#endif
    address.sin_family = AF_INET;
    address.sin_port = htons(port);
    result->connect_stage=1;
    if (inet_pton(AF_INET, ip, &address.sin_addr) != 1) { result->posix_errno=errno; return -1; }
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
