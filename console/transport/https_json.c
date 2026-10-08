/* SPDX-License-Identifier: GPL-3.0-or-later */
#define _GNU_SOURCE 1
#include "https_json.h"
#include <mbedtls/ctr_drbg.h>
#include <mbedtls/entropy.h>
#include <mbedtls/ssl.h>
#include <mbedtls/x509_crt.h>
#include <mbedtls/net_sockets.h>
#include <mbedtls/platform_util.h>
#include <arpa/inet.h>
#include <errno.h>
#include <fcntl.h>
#include <netinet/in.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <sys/select.h>
#include <sys/socket.h>
#include <time.h>
#include <unistd.h>
#include "https_io.h"

static int retry(int rc) { return rc==MBEDTLS_ERR_SSL_WANT_READ||rc==MBEDTLS_ERR_SSL_WANT_WRITE; }
static int header_value(const char *value,size_t limit) {
    if(!value||strlen(value)>limit)return 0;
    for(const unsigned char *p=(const unsigned char*)value;*p;p++) if(*p<33||*p>126)return 0;
    return 1;
}
JsonResponse https_json(const char *ip,unsigned short port,const char *name,
                        const char *ca,const char *path,const char *token,
                        const char *json,char *body,size_t capacity) {
    JsonResponse result={.tls={.rc=-1}};
    if(body&&capacity)body[0]=0;
    if(!body||capacity<2||capacity>65536||!header_value(ip,64)||!header_value(name,192)||
       !path||strncmp(path,"/api/device/",12)||!header_value(path,128)||
       !ca||!ca[0]||!json||strlen(json)>8192||(token&&!header_value(token,128)))return result;
    for(const char *p=path;*p;p++)if(!((*p>='a'&&*p<='z')||*p=='/'))return result;
    int64_t now=monotonic_ms();if(now<0)return result;
    Connection connection={.fd=-1,.deadline=now+15000};
    struct HttpWorkspace {char request[9216],headers[8192];};
    struct HttpWorkspace *workspace=calloc(1,sizeof(*workspace));
    if(!workspace)return result;
    mbedtls_entropy_context entropy;mbedtls_ctr_drbg_context rng;
    mbedtls_ssl_context tls;mbedtls_ssl_config config;mbedtls_x509_crt roots;
    mbedtls_entropy_init(&entropy);mbedtls_ctr_drbg_init(&rng);
    mbedtls_ssl_init(&tls);mbedtls_ssl_config_init(&config);mbedtls_x509_crt_init(&roots);
    const unsigned char label[]="ps5-sync-device-json";
    int rc=mbedtls_ctr_drbg_seed(&rng,mbedtls_entropy_func,&entropy,label,sizeof(label)-1);
    if(rc)goto finished;
    rc=mbedtls_x509_crt_parse(&roots,(const unsigned char*)ca,strlen(ca)+1);if(rc)goto finished;
    rc=mbedtls_ssl_config_defaults(&config,MBEDTLS_SSL_IS_CLIENT,MBEDTLS_SSL_TRANSPORT_STREAM,MBEDTLS_SSL_PRESET_DEFAULT);if(rc)goto finished;
    mbedtls_ssl_conf_authmode(&config,MBEDTLS_SSL_VERIFY_REQUIRED);
    mbedtls_ssl_conf_ca_chain(&config,&roots,NULL);mbedtls_ssl_conf_rng(&config,mbedtls_ctr_drbg_random,&rng);
    mbedtls_ssl_conf_min_tls_version(&config,MBEDTLS_SSL_VERSION_TLS1_2);
    mbedtls_ssl_conf_max_tls_version(&config,MBEDTLS_SSL_VERSION_TLS1_2);
    rc=mbedtls_ssl_setup(&tls,&config);if(rc)goto finished;
    rc=mbedtls_ssl_set_hostname(&tls,name);if(rc)goto finished;
    connection.fd=connect_bounded(ip,port,&result.tls);
    if(connection.fd<0){rc=MBEDTLS_ERR_NET_CONNECT_FAILED;goto finished;}
    mbedtls_ssl_set_bio(&tls,&connection,transmit,receive,NULL);
    do{rc=mbedtls_ssl_handshake(&tls);}while(retry(rc)&&monotonic_ms()<connection.deadline);
    result.tls.verify_flags=mbedtls_ssl_get_verify_result(&tls);
    if(rc||result.tls.verify_flags){if(!rc)rc=-1;goto finished;}
    result.tls.verified_handshake=1;
    char *request=workspace->request;
    int n=snprintf(request,sizeof(workspace->request),"POST %s HTTP/1.1\r\nHost: %s:%u\r\nContent-Type: application/json\r\nAccept: application/json\r\nConnection: close\r\nContent-Length: %zu\r\n%s%s%s\r\n%s",
                   path,name,(unsigned)port,strlen(json),token?"Authorization: Bearer ":"",token?token:"",token?"\r\n":"",json);
    if(n<0||(size_t)n>=sizeof(workspace->request)){rc=-1;goto finished;}
    size_t sent=0;
    while(sent<(size_t)n){
        rc=mbedtls_ssl_write(&tls,(unsigned char*)request+sent,(size_t)n-sent);
        if(retry(rc)&&monotonic_ms()<connection.deadline)continue;
        if(rc<=0)goto finished;
        sent+=(size_t)rc;
    }
    char *headers=workspace->headers;size_t used=0;char *end=NULL;
    while(used<sizeof(workspace->headers)-1){
        rc=mbedtls_ssl_read(&tls,(unsigned char*)headers+used,1);
        if(retry(rc)&&monotonic_ms()<connection.deadline)continue;
        if(rc<=0){rc=-1;goto finished;}
        used++;headers[used]=0;
        if(used>=4&&!memcmp(headers+used-4,"\r\n\r\n",4)){end=headers+used-2;break;}
    }
    if(!end||used<17||strncmp(headers,"HTTP/1.1 ",9)||headers[9]<'1'||headers[9]>'5'||headers[10]<'0'||headers[10]>'9'||headers[11]<'0'||headers[11]>'9'||headers[12]!=' '){rc=-1;goto finished;}
    result.status=(headers[9]-'0')*100+(headers[10]-'0')*10+headers[11]-'0';
    int has_length=0;size_t length=0;
    char *line=strstr(headers,"\r\n");if(!line){rc=-1;goto finished;}line+=2;
    while(line<end){
        char *next=strstr(line,"\r\n"),*colon=strchr(line,':');
        if(!next||!colon||colon>=next||line[0]==' '||line[0]=='\t'){rc=-1;goto finished;}
        *colon=0;*next=0;char *v=colon+1;while(*v==' '||*v=='\t')v++;
        if(!strcasecmp(line,"Transfer-Encoding")){rc=-1;goto finished;}
        if(!strcasecmp(line,"Content-Length")){
            if(has_length++||!*v){rc=-1;goto finished;}
            for(;*v;v++){if(*v<'0'||*v>'9'||length>(capacity-1)/10){rc=-1;goto finished;}length=length*10+(unsigned)(*v-'0');if(length>=capacity){rc=-1;goto finished;}}
        }
        line=next+2;
    }
    if(!has_length){rc=-1;goto finished;}
    while(result.size<length){
        rc=mbedtls_ssl_read(&tls,(unsigned char*)body+result.size,length-result.size);
        if(retry(rc)&&monotonic_ms()<connection.deadline)continue;
        if(rc<=0){rc=-1;goto finished;}result.size+=(size_t)rc;
    }
    body[result.size]=0;rc=0;
finished:
    result.tls.rc=rc;
    if(rc){body[0]=0;result.size=0;}
    if(connection.fd>=0)close(connection.fd);
    mbedtls_ssl_free(&tls);mbedtls_ssl_config_free(&config);mbedtls_x509_crt_free(&roots);
    mbedtls_ctr_drbg_free(&rng);mbedtls_entropy_free(&entropy);
    mbedtls_platform_zeroize(workspace,sizeof(*workspace));free(workspace);
    return result;
}
