/* SPDX-License-Identifier: GPL-3.0-or-later */
#define _GNU_SOURCE 1
#include "native_discovery_ftp.h"
#include <errno.h>
#include <fcntl.h>
#include <netinet/in.h>
#include <sys/select.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <time.h>
#include <unistd.h>
static int alive(time_t deadline){struct timespec now;return !clock_gettime(CLOCK_MONOTONIC,&now)&&now.tv_sec<deadline;}
static int local_connect(unsigned short port){
    int fd=socket(AF_INET,SOCK_STREAM|SOCK_NONBLOCK,0);if(fd<0)return -1;
    if(fd>=FD_SETSIZE){close(fd);return -1;}
    struct sockaddr_in address={0};
#ifdef PS5_DIAGNOSTIC_SOCKET
    address.sin_len=sizeof(address);
#endif
    address.sin_family=AF_INET;address.sin_port=htons(port);address.sin_addr.s_addr=htonl(0x7f000001u);
    int flags=fcntl(fd,F_GETFL,0);if(flags<0||!(flags&O_NONBLOCK)){close(fd);return -1;}
    int rc=connect(fd,(struct sockaddr*)&address,sizeof(address));if(rc&&errno!=EINPROGRESS){close(fd);return -1;}
    if(rc){fd_set write;FD_ZERO(&write);FD_SET(fd,&write);struct timeval wait={2,0};int error=0;socklen_t size=sizeof(error);
        if(select(fd+1,NULL,&write,NULL,&wait)!=1||getsockopt(fd,SOL_SOCKET,SO_ERROR,&error,&size)||error){close(fd);return -1;}}
    return fd;
}
static ssize_t transfer(int fd,void *body,size_t size,int writing,time_t deadline){
    while(alive(deadline)){fd_set ready;FD_ZERO(&ready);FD_SET(fd,&ready);struct timeval wait={2,0};
        int rc=select(fd+1,writing?NULL:&ready,writing?&ready:NULL,NULL,&wait);if(rc<=0)return -1;
        ssize_t n=writing?send(fd,body,size,0):recv(fd,body,size,0);
        if(n>=0)return n;if(errno!=EAGAIN&&errno!=EWOULDBLOCK&&errno!=EINTR)return -1;}
    return -1;
}
static int line(int fd,char output[1024],time_t deadline){
    size_t n=0;while(n<1023&&alive(deadline)){if(transfer(fd,output+n,1,0,deadline)!=1)return -1;if(output[n++]=='\n'){output[n]=0;return 0;}}return -1;
}
static int reply(int fd,char output[1024],time_t deadline,int *version){
    for(unsigned i=0;i<16;i++){
        if(line(fd,output,deadline))return -1;
        if(version&&strstr(output,"Version: v0.21.1 ("))*version=1;
        if(strlen(output)<5||output[0]<'1'||output[0]>'5'||output[1]<'0'||output[1]>'9'||output[2]<'0'||output[2]>'9')return -1;
        if(output[3]==' ')return atoi(output);if(output[3]!='-')return -1;
    }return -1;
}
static int command(int fd,const char *text,char response[1024],time_t deadline){
    size_t at=0,size=strlen(text);while(at<size&&alive(deadline)){ssize_t n=transfer(fd,(void*)(text+at),size-at,1,deadline);if(n<=0)return -1;at+=(size_t)n;}
    return at==size?reply(fd,response,deadline,NULL):-1;
}
int native_discover(unsigned profile,char titles[128][13],unsigned *count){
    if(!titles||!count)return -1;*count=0;struct timespec now;if(clock_gettime(CLOCK_MONOTONIC,&now))return -1;time_t deadline=now.tv_sec+15;
    unsigned port=2121;
#ifdef NATIVE_DISCOVERY_TEST
    const char *configured=getenv("MOCK_FTP_PORT");if(!configured)return -1;port=(unsigned)atoi(configured);
#endif
    int control=local_connect((unsigned short)port),data=-1,rc=-1,version=0,stage=2;char response[1024],cwd[256];if(control<0)return -1;
    if(reply(control,response,deadline,&version)!=220||!version)goto done;
    stage=3;int login=command(control,"USER anonymous\r\n",response,deadline);
    if(login==331)login=command(control,"PASS anonymous\r\n",response,deadline);if(login!=230)goto done;
    snprintf(cwd,sizeof(cwd),"CWD /user/home/%08x/trophy2/nobackup/data\r\n",profile);
    stage=4;if(command(control,cwd,response,deadline)!=250)goto done;
    stage=5;if(command(control,"PASV\r\n",response,deadline)!=227)goto done;
    char *start=strchr(response,'(');unsigned a,b,c,d,high,low;int consumed=0;
    if(!start||sscanf(start,"(%u,%u,%u,%u,%u,%u)%n",&a,&b,&c,&d,&high,&low,&consumed)!=6||consumed<=0||a>255||b>255||c>255||d>255||high>255||low>255||!(high*256+low))goto done;
    /* Always loopback: never follow an advertised FTP host. */
    stage=6;data=local_connect((unsigned short)(high*256+low));if(data<0)goto done;
    stage=7;int status=command(control,"MLSD\r\n",response,deadline);if(status!=150&&status!=125)goto done;
    stage=8;char listing[65537];size_t used=0;
    while(alive(deadline)){
        ssize_t n=transfer(data,listing+used,sizeof(listing)-1-used,0,deadline);if(n<0)goto done;if(!n)break;used+=(size_t)n;if(used==sizeof(listing)-1)goto done;
    }
    if(!alive(deadline))goto done;listing[used]=0;close(data);data=-1;
    stage=9;if(reply(control,response,deadline,NULL)!=226)goto done;
    stage=10;char *row=listing;
    while(*row){char *end=strstr(row,"\r\n");if(!end)goto done;*end=0;
        char *name=strchr(row,' ');
        if(!strncmp(row,"type=dir;",9)&&name){name++;int valid=strlen(name)==12&&!strncmp(name,"NPWR",4)&&!strcmp(name+9,"_00");
            for(unsigned i=4;valid&&i<9;i++)if(name[i]<'0'||name[i]>'9')valid=0;
            if(valid){int duplicate=0;for(unsigned i=0;i<*count;i++)if(!strcmp(titles[i],name))duplicate=1;
                if(!duplicate){if(*count==128)goto done;memcpy(titles[(*count)++],name,13);}}
        }row=end+2;
    }
    rc=0;
done:if(data>=0)close(data);close(control);if(rc)*count=0;return rc?-stage:0;
}
