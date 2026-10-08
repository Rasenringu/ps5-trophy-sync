/* SPDX-License-Identifier: GPL-3.0-or-later */
/* MOCK console loopback protocol only; never connects to PS5. */
#include "../worker/status.h"
#include <assert.h>
#include <netinet/in.h>
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/wait.h>
#include <unistd.h>
static const char *origin="https://MOCK.example.test";
static WorkerStatus sample(void){
    WorkerStatus s={.magic="PS5ST1",.version=1,.profile=123};
    s.model.close_with_shell=true;s.model.phase=UI_CONNECTED;
    snprintf(s.model.public_origin,sizeof(s.model.public_origin),"%s",origin);
    snprintf(s.model.profile,sizeof(s.model.profile),"MOCK profile");return s;
}
static void exchange(int truncated){
    int listener=socket(AF_INET,SOCK_STREAM,0),enabled=1;assert(listener>=0);
    assert(!setsockopt(listener,SOL_SOCKET,SO_REUSEADDR,&enabled,sizeof(enabled)));
    struct sockaddr_in address={.sin_family=AF_INET,.sin_port=htons(WORKER_STATUS_PORT),.sin_addr={htonl(INADDR_LOOPBACK)}};
    assert(!bind(listener,(struct sockaddr*)&address,sizeof(address))&&!listen(listener,1));
    pid_t child=fork();assert(child>=0);
    if(!child){
        int peer=accept(listener,NULL,NULL);assert(peer>=0);WorkerRequest request;
        assert(!worker_transfer(peer,&request,sizeof(request),0));assert(!memcmp(request.magic,"PS5UI1\0",8)&&request.profile==123&&!request.reserved);
        WorkerStatus status=sample();assert(!worker_transfer(peer,&status,truncated?sizeof(status)/2:sizeof(status),1));close(peer);close(listener);_exit(0);
    }
    WorkerStatus status;int rc=worker_status_fetch(123,&status);assert(truncated?rc==-1:rc==0&&worker_status_valid(&status,123,origin));
    close(listener);int result=0;assert(waitpid(child,&result,0)==child&&WIFEXITED(result)&&WEXITSTATUS(result)==0);
}
int main(void){
    WorkerStatus s=sample();assert(worker_status_valid(&s,123,origin));
    assert(!worker_status_valid(&s,124,origin));s.profile=124;assert(!worker_status_valid(&s,123,origin));s=sample();
    s.model.phase=UI_PAIRING;s.ttl_seconds=30;snprintf(s.model.manual_code,sizeof(s.model.manual_code),"ABCD-2345");assert(worker_status_valid(&s,123,origin));
    s.ttl_seconds=0;assert(!worker_status_valid(&s,123,origin));s.ttl_seconds=601;assert(!worker_status_valid(&s,123,origin));
    s=sample();s.model.expires_at_ms=123;assert(!worker_status_valid(&s,123,origin));
    s=sample();memset(s.model.error,'X',sizeof(s.model.error));assert(!worker_status_valid(&s,123,origin));
    s=sample();memset(s.model.sync_status,'X',sizeof(s.model.sync_status));assert(!worker_status_valid(&s,123,origin));
    s=sample();s.version=2;assert(!worker_status_valid(&s,123,origin));
    s=sample();*(unsigned char*)&s.model.mock=2;assert(!worker_status_valid(&s,123,origin));
    s=sample();s.model.phase=(UiPhase)-1;assert(!worker_status_valid(&s,123,origin));
    s=sample();snprintf(s.model.public_origin,sizeof(s.model.public_origin),"https://EVIL.test");assert(!worker_status_valid(&s,123,origin));
    exchange(0);exchange(1);
    puts("PASS MOCK loopback status: scoped profile/origin/phase/TTL and string bounds; fragmented/truncated wire handling, invalid bool representation rejected. No credentials in model.");
}
