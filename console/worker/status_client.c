/* SPDX-License-Identifier: GPL-3.0-or-later */
#define _GNU_SOURCE 1
#include "status_client.h"
#include <errno.h>
#include <fcntl.h>
#include <netinet/in.h>
#include <string.h>
#include <sys/select.h>
#include <sys/socket.h>
#include <time.h>
#include <unistd.h>
static unsigned connect_stage;
static int connect_error;
unsigned worker_connect_stage(void){return connect_stage;}
int worker_connect_errno(void){return connect_error;}
static int64_t status_ms(void){struct timespec ts;if(clock_gettime(CLOCK_MONOTONIC,&ts))return -1;return (int64_t)ts.tv_sec*1000+ts.tv_nsec/1000000;}
int worker_loopback_connect(unsigned short port){
    connect_stage=1;connect_error=0;
    int fd=socket(AF_INET,SOCK_STREAM|SOCK_NONBLOCK,0);if(fd<0){connect_error=errno;return -1;}
    if(fd>=FD_SETSIZE){connect_error=EMFILE;close(fd);return -1;}
    struct sockaddr_in address={0};
#ifdef PS5_DIAGNOSTIC_SOCKET
    address.sin_len=sizeof(address);
#endif
    address.sin_family=AF_INET;address.sin_port=htons(port);address.sin_addr.s_addr=htonl(WORKER_LOOPBACK_ADDRESS);
    connect_stage=2;int flags=fcntl(fd,F_GETFL,0);
    if(flags<0||!(flags&O_NONBLOCK)){connect_error=flags<0?errno:EOPNOTSUPP;close(fd);return -1;}
    connect_stage=3;int rc=connect(fd,(struct sockaddr*)&address,sizeof(address));
    if(rc&&errno!=EINPROGRESS){connect_error=errno;close(fd);return -1;}
    if(rc){
        connect_stage=4;fd_set write;FD_ZERO(&write);FD_SET(fd,&write);struct timeval timeout={2,0};int error=0;socklen_t length=sizeof(error);
        int ready=select(fd+1,NULL,&write,NULL,&timeout);
        if(ready!=1){connect_error=ready==0?ETIMEDOUT:errno;close(fd);return -1;}
        connect_stage=5;
        if(getsockopt(fd,SOL_SOCKET,SO_ERROR,&error,&length)||error){connect_error=error?error:errno;close(fd);return -1;}
    }
    connect_stage=6;return fd;
}
int worker_transfer(int fd,void *bytes,size_t size,int sending){
    if(fd<0||fd>=FD_SETSIZE||!bytes||size>4096)return -1;
    int64_t started=status_ms();if(started<0)return -1;size_t used=0;
    while(used<size){
        int64_t now=status_ms(),remaining=started+3000-now;if(now<0||remaining<=0){errno=ETIMEDOUT;return -1;}
        struct timeval timeout={remaining/1000,(remaining%1000)*1000};fd_set ready;FD_ZERO(&ready);FD_SET(fd,&ready);
        int rc=select(fd+1,sending?NULL:&ready,sending?&ready:NULL,NULL,&timeout);
        if(rc<0&&errno==EINTR)continue;
        if(rc!=1){if(!rc)errno=ETIMEDOUT;return -1;}
        ssize_t n=sending?send(fd,(char*)bytes+used,size-used,0):recv(fd,(char*)bytes+used,size-used,0);
        if(n<0&&(errno==EAGAIN||errno==EWOULDBLOCK||errno==EINTR))continue;
        if(n<=0)return -1;
        used+=(size_t)n;
    }
    return 0;
}
int worker_status_fetch(unsigned profile,WorkerStatus *status){
    int fd=worker_loopback_connect(WORKER_STATUS_PORT);if(fd<0)return -1;
    WorkerRequest request={.magic="PS5UI1",.profile=profile};
    int rc=worker_transfer(fd,&request,sizeof(request),1)||worker_transfer(fd,status,sizeof(*status),0);close(fd);return rc?-1:0;
}
int worker_status_valid(const WorkerStatus *status,unsigned profile,const char *origin){
    if(!status||!origin||memcmp(status->magic,"PS5ST1\0",8)||status->version!=1||status->profile!=profile||
       status->reserved||status->ttl_seconds>600)return 0;
    const UiModel *model=&status->model;
    if(*(const unsigned char*)&model->mock>1||*(const unsigned char*)&model->close_with_shell>1)return 0;
    if(!memchr(model->profile,0,sizeof(model->profile))||!memchr(model->public_origin,0,sizeof(model->public_origin))||
       !memchr(model->manual_code,0,sizeof(model->manual_code))||!memchr(model->error,0,sizeof(model->error))||
       !memchr(model->reader_status,0,sizeof(model->reader_status))||!memchr(model->sync_status,0,sizeof(model->sync_status))||model->phase>UI_DIAGNOSTIC||model->phase<UI_UNAVAILABLE||
       model->mock||!model->close_with_shell||model->expires_at_ms||strcmp(model->public_origin,origin))return 0;
    if(model->phase==UI_PAIRING){
        UiModel checked=*model;return status->ttl_seconds&&ui_set_pairing(&checked,origin,model->manual_code,0,status->ttl_seconds);
    }
    return !model->manual_code[0]&&!status->ttl_seconds;
}
