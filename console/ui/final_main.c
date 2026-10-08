/* Foreground presentation update; worker IPC and native launch path preserved. */
/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Direct VideoOut frontend. API/layout constants researched in the pinned
 * BlackBearReloaded template; foreground VideoOut path previously user-verified.
 */
#include "final_screen.h"
#include "tiled_frame.h"
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <pthread.h>
#include <stdatomic.h>
#include "probe_config.h"
#include "final_worker_config.h"
#include "../worker/status_client.h"
#include <sys/socket.h>
#include <sys/select.h>
#include <errno.h>
#include <unistd.h>

struct Notification { uint8_t reserved[45]; char message[3075]; };
struct Buffer { void *data, *metadata, *reserved0, *reserved1; };
struct Attribute { uint8_t reserved[80]; };
extern int sceKernelSendNotificationRequest(uint32_t, void *, size_t, int);
extern int sceKernelUsleep(uint32_t);
extern uint64_t sceKernelGetProcessTime(void);
extern size_t sceKernelGetDirectMemorySize(void);
extern int sceKernelAllocateDirectMemory(int64_t,int64_t,size_t,size_t,int,int64_t*);
extern int sceKernelMapDirectMemory(void**,size_t,int,int,int64_t,size_t);
extern int sceSystemServiceHideSplashScreen(void);
extern int sceVideoOutOpen(int32_t,int32_t,int32_t,const void*);
extern int sceVideoOutSetFlipRate(int32_t,int32_t);
extern void sceVideoOutSetBufferAttribute2(struct Attribute*,uint64_t,uint32_t,uint32_t,uint32_t,uint64_t,uint32_t,uint64_t);
extern int sceVideoOutRegisterBuffers2(int32_t,int32_t,int32_t,struct Buffer*,int32_t,struct Attribute*,int32_t,void*);
extern int sceVideoOutSubmitFlip(int32_t,int32_t,uint32_t,int64_t);
extern int sceVideoOutWaitVblank(int32_t);

static void notify(const char *message) {
    struct Notification note={0};
    size_t i = 0;
    for (; message[i] && i < sizeof(note.message)-1; i++) note.message[i] = message[i];
    note.message[i] = 0;
    (void)sceKernelSendNotificationRequest(0, &note, sizeof(note), 0);
}
static void hold(void) __attribute__((noreturn));
static void hold(void) { for (;;) (void)sceKernelUsleep(1000000); }
static void fail(const char *action, int rc) __attribute__((noreturn));
static void fail(const char *action, int rc) {
    char message[200];
    snprintf(message, sizeof(message), "Trophy Sync: %s failed (%d). PS button > Close App.", action, rc);
    notify(message); hold();
}
static void flush(void *address) {
    for (size_t i = 0; i < DIRECT_FRAME_BYTES; i += 64)
        __asm__ volatile("clflush (%0)" : : "r"((uint8_t*)address + i) : "memory");
    __asm__ volatile("mfence" ::: "memory");
}
extern int sceUserServiceInitialize(void *);
extern int sceUserServiceGetForegroundUser(uint32_t *);
/* Signature checked in pinned SDL PS5 joystick header (ee4c47dc...).
 * Read-only optional label; a failed lookup retains the active-profile fallback. */
extern int sceUserServiceGetUserName(int,char *,size_t);
static pthread_mutex_t model_lock;
static UiModel live_model;
static atomic_int profile_changed;
static unsigned selected_profile;
static char selected_name[64];
static void publish(const UiModel *model) {
    pthread_mutex_lock(&model_lock);live_model=*model;pthread_mutex_unlock(&model_lock);
}
static unsigned manager_stage;static int manager_errno,manager_http;
static int manager_get(const char *path,char output[2048]) {
    manager_stage=1;manager_errno=manager_http=0;int fd=worker_loopback_connect(8084);if(fd<0){manager_errno=worker_connect_errno();return -1;}
    manager_stage=2;char request[512];int length=snprintf(request,sizeof(request),"GET %s HTTP/1.1\r\nHost: 127.0.0.1:8084\r\nConnection: close\r\n\r\n",path);
    if(length<0||(size_t)length>=sizeof(request)||worker_transfer(fd,request,(size_t)length,1)){manager_errno=errno;close(fd);return -1;}
    manager_stage=3;size_t used=0;uint64_t began=sceKernelGetProcessTime()/1000;
    while(used<2047){
        uint64_t now=sceKernelGetProcessTime()/1000;if(now-began>=5000){manager_errno=ETIMEDOUT;close(fd);return -1;}
        unsigned remaining=(unsigned)(5000-(now-began));struct timeval timeout={remaining/1000,(remaining%1000)*1000};fd_set ready;FD_ZERO(&ready);FD_SET(fd,&ready);
        int selected=select(fd+1,&ready,NULL,NULL,&timeout);if(selected<0&&errno==EINTR)continue;
        if(selected!=1){manager_errno=selected==0?ETIMEDOUT:errno;close(fd);return -1;}
        ssize_t n=recv(fd,output+used,2047-used,0);if(n<0&&(errno==EAGAIN||errno==EWOULDBLOCK||errno==EINTR))continue;
        if(n<0){manager_errno=errno;close(fd);return -1;}if(!n)break;used+=(size_t)n;
    }
    close(fd);output[used]=0;manager_stage=4;
    if(used>=12&&output[9]>='0'&&output[9]<='9'&&output[10]>='0'&&output[10]<='9'&&output[11]>='0'&&output[11]<='9')manager_http=(output[9]-'0')*100+(output[10]-'0')*10+output[11]-'0';
    if(used>=2047||(strncmp(output,"HTTP/1.1 200 ",13)&&strncmp(output,"HTTP/1.0 200 ",13)))return -1;
    char *body=strstr(output,"\r\n\r\n");if(!body)return -1;body+=4;
    memmove(output,body,strlen(body)+1);manager_stage=5;return 0;
}
static void bridge_error(UiModel *model,const char *action) {
    model->phase=UI_ERROR;model->manual_code[0]=0;
    snprintf(model->error,sizeof(model->error),"%s. Close App; leave it closed if a crash occurs.",action);
    snprintf(model->sync_status,sizeof(model->sync_status),"Sync unavailable: %s",action);
    snprintf(model->reader_status,sizeof(model->reader_status),"Connector stage %u errno %d; Manager stage %u errno %d HTTP %d",worker_connect_stage(),worker_connect_errno(),manager_stage,manager_errno,manager_http);publish(model);
}
static void *network_worker(void *unused) {
    (void)unused;UiModel model={.mock=false,.close_with_shell=true};WorkerStatus status;
    snprintf(model.profile,sizeof(model.profile),"Local profile %08X",selected_profile);
    char origin[192];snprintf(origin,sizeof(origin),"https://%s:%u",PROBE_IP,PROBE_PORT);
    snprintf(model.public_origin,sizeof(model.public_origin),"%s",origin);
    int available=!worker_status_fetch(selected_profile,&status);
    if(!available){
        char body[2048];
        if(manager_get("/version",body)||strncmp(body,"0.5.2",5)||strspn(body+5,"\r\n ")!=strlen(body+5)){bridge_error(&model,"Payload Manager loopback/version unavailable");return NULL;}
        if(atomic_load(&profile_changed))return NULL;
        if(manager_get("/loadpayload:" WORKER_FILENAME,body)){bridge_error(&model,"Console worker launch failed");return NULL;}
        uint64_t deadline=sceKernelGetProcessTime()/1000+12000;
        while(!atomic_load(&profile_changed)&&sceKernelGetProcessTime()/1000<deadline){
            if(!worker_status_fetch(selected_profile,&status)){available=1;break;}sceKernelUsleep(250000);
        }
    }
    if(!available){bridge_error(&model,"Console worker status unavailable");return NULL;}
    while(!atomic_load(&profile_changed)){
        if(!worker_status_valid(&status,selected_profile,origin)){bridge_error(&model,"Worker profile/status validation failed");return NULL;}
        model=status.model;
        if(selected_name[0])snprintf(model.profile,sizeof(model.profile),"%s",selected_name);
        char code[10];memcpy(code,model.manual_code,sizeof(code));
        if(model.phase==UI_PAIRING&&!ui_set_pairing(&model,origin,code,sceKernelGetProcessTime()/1000,status.ttl_seconds)){bridge_error(&model,"Worker pairing code/expiry invalid");return NULL;}
        publish(&model);sceKernelUsleep(500000);
        if(worker_status_fetch(selected_profile,&status)){bridge_error(&model,"Console worker disconnected");return NULL;}
    }
    return NULL;
}
int main(void) {
    uint32_t *pixels = malloc((size_t)SCREEN_WIDTH * SCREEN_HEIGHT * 4);
    if (!pixels) fail("pixel allocation", -1);
    (void)sceSystemServiceHideSplashScreen();
    int video = sceVideoOutOpen(0xff, 0, 0, NULL);
    if (video < 0) fail("VideoOut open", video);
    size_t capacity = sceKernelGetDirectMemorySize();
    if (capacity < DIRECT_POOL_BYTES) fail("direct memory capacity", -1);
    int64_t physical = 0;
    int rc = sceKernelAllocateDirectMemory(0, (int64_t)capacity, DIRECT_POOL_BYTES, 0x200000, 3, &physical);
    if (rc < 0) fail("direct memory allocation", rc);
    void *mapped = NULL;
    rc = sceKernelMapDirectMemory(&mapped, DIRECT_POOL_BYTES, 0x33, 0, physical, 0x200000);
    if (rc < 0 || !mapped) fail("direct memory mapping", rc);
    struct Buffer buffers[2] = {{mapped,NULL,NULL,NULL},{(uint8_t*)mapped+DIRECT_FRAME_BYTES,NULL,NULL,NULL}};
    struct Attribute attr = {{0}};
    rc = sceVideoOutSetFlipRate(video, 0);
    if (rc < 0) fail("flip rate", rc);
    sceVideoOutSetBufferAttribute2(&attr, UINT64_C(0x8000000022000000), 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0);
    rc = sceVideoOutRegisterBuffers2(video, 0, 0, buffers, 2, &attr, 0, NULL);
    if (rc < 0) fail("buffer registration", rc);
    UiModel model={.mock=false,.close_with_shell=true};
    snprintf(model.error,sizeof(model.error),"Connecting the console reader to the selected profile...");
    int users=sceUserServiceInitialize(NULL);
    if(users || sceUserServiceGetForegroundUser(&selected_profile) || selected_profile==0xffffffffu) {
        model.phase=UI_ERROR;snprintf(model.error,sizeof(model.error),"Selected profile query failed. Close App.");
    }else{
        snprintf(model.profile,sizeof(model.profile),"Local profile %08X",selected_profile);
        if(!sceUserServiceGetUserName((int)selected_profile,selected_name,sizeof(selected_name))&&memchr(selected_name,0,sizeof(selected_name))&&selected_name[0])
            snprintf(model.profile,sizeof(model.profile),"%s",selected_name);
        else memset(selected_name,0,sizeof(selected_name));
        if(pthread_mutex_init(&model_lock,NULL))fail("pairing model lock",-1);
        live_model=model;pthread_t thread;
        pthread_attr_t attributes;
        size_t stack_size=0;
        if(pthread_attr_init(&attributes))fail("worker attributes",-1);
        if(pthread_attr_setstacksize(&attributes,1024*1024))fail("worker stack size",-1);
        if(pthread_attr_getstacksize(&attributes,&stack_size)||stack_size<1024*1024)fail("worker stack verification",-1);
        if(pthread_create(&thread,&attributes,network_worker,NULL))fail("HTTPS worker creation",-1);
        (void)pthread_attr_destroy(&attributes);
        (void)pthread_detach(thread);
    }
    unsigned back = 0;
    for (int64_t frame = 1;; frame++) {
        if(model.profile[0]){
            unsigned current=0xffffffffu;
            if(sceUserServiceGetForegroundUser(&current)||current!=selected_profile)atomic_store(&profile_changed,1);
            if(atomic_load(&profile_changed)){
                model.phase=UI_ERROR;model.manual_code[0]=0;
                snprintf(model.error,sizeof(model.error),"Profile changed. Close App and reopen for that profile.");
            }else{pthread_mutex_lock(&model_lock);model=live_model;pthread_mutex_unlock(&model_lock);}
        }
        ui_render_final(pixels, &model, sceKernelGetProcessTime()/1000);
        ui_tile_frame(buffers[back].data, pixels); flush(buffers[back].data);
        rc = sceVideoOutSubmitFlip(video, (int32_t)back, 1, frame);
        if (rc < 0) fail("frame submission", rc);
        rc = sceVideoOutWaitVblank(video);
        if (rc < 0) fail("vblank wait", rc);
        back ^= 1u;
        (void)sceKernelUsleep(100000);
    }
}
