/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Specifically authorized diagnostic only. System mount API receives ONLY a
 * disposable private copy. No original mounts, copy-back, trophy APIs or sync. */
#include "../readers/ps4_image_snapshot.h"
#include "../readers/schema_probe.h"
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <ps5/kernel.h>
#include <sqlite3.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/stat.h>
#include <unistd.h>
#define STAGE "/data/trophy-sync-ps4-inspect"
typedef struct {uint8_t reserved;char *budgetid;} MountOpt;
typedef struct {uint8_t dummy;} UnmountOpt;
static int (*sceFsInitMountTrophyDataOpt)(MountOpt*);
static int (*sceFsMountTrophyData)(MountOpt*,const char*,const char*,uint8_t*);
static int (*sceFsInitUmountTrophyDataOpt)(UnmountOpt*);
static int (*sceFsUmountTrophyData)(UnmountOpt*,const char*,int,int);
extern int sceUserServiceGetForegroundUser(uint32_t*);
extern int sceUserServiceInitialize(void*);
int __patch_init(void){return 0;}
static uint32_t selected;
static FILE *report;
static void erase(void *memory,size_t size){volatile unsigned char *p=memory;while(size--)*p++=0;}
static int same_user(void){uint32_t p=UINT32_MAX;return !sceUserServiceGetForegroundUser(&p)&&p==selected;}
static int title_ok(const char *n){if(!strcmp(n,"sce_trop"))return 1;if(strlen(n)!=12||strncmp(n,"NPWR",4)||strcmp(n+9,"_00"))return 0;for(int i=4;i<9;i++)if(n[i]<'0'||n[i]>'9')return 0;return 1;}
static void checkpoint(const char *text){fprintf(report,"%s\n",text);fflush(report);fsync(fileno(report));}
static int load_fs(void){
    uint32_t fs=0;
    int (*load)(const char*,size_t,const void*,unsigned,void*,int*)=(void*)kernel_dynlib_dlsym(-1,1,"sceKernelLoadStartModule");
    if(!load)load=(void*)kernel_dynlib_dlsym(-1,0x2001,"sceKernelLoadStartModule");if(!load)return -2;
    checkpoint("loading filesystem library only; no trophy library or dlopen");
    int rc=load("/system/priv/lib/libSceFsInternalForVsh.sprx",0,NULL,0,NULL,NULL);
    fprintf(report,"filesystem_load_rc=%d\n",rc);if(rc<0)return -3;fs=(uint32_t)rc;
    sceFsInitMountTrophyDataOpt=(void*)kernel_dynlib_dlsym(-1,fs,"sceFsInitMountTrophyDataOpt");
    sceFsMountTrophyData=(void*)kernel_dynlib_dlsym(-1,fs,"sceFsMountTrophyData");
    sceFsInitUmountTrophyDataOpt=(void*)kernel_dynlib_dlsym(-1,fs,"sceFsInitUmountTrophyDataOpt");
    sceFsUmountTrophyData=(void*)kernel_dynlib_dlsym(-1,fs,"sceFsUmountTrophyData");
    return sceFsInitMountTrophyDataOpt&&sceFsMountTrophyData&&sceFsInitUmountTrophyDataOpt&&sceFsUmountTrophyData?0:-5;
}
static void inspect_db(const char *path){
    SchemaProbe probe=schema_probe(path);fprintf(report,"database rc=%d transaction=%d journal=%s\n",probe.rc,probe.read_transaction,probe.journal_mode);
    if(!probe.read_transaction||strcmp(probe.journal_mode,"delete"))return;
    sqlite3 *db=NULL;sqlite3_stmt *q=NULL;
    if(sqlite3_open_v2(path,&db,SQLITE_OPEN_READONLY|SQLITE_OPEN_NOFOLLOW,"ps5-sync-deny-write")){sqlite3_close(db);return;}
    sqlite3_busy_timeout(db,1000);
    if(sqlite3_exec(db,"PRAGMA query_only=ON; BEGIN",NULL,NULL,NULL))goto done;
    if(!sqlite3_prepare_v2(db,"SELECT name,sql FROM sqlite_schema WHERE type='table' AND name GLOB 'tbl_trophy*' LIMIT 32",-1,&q,NULL)){
        while(sqlite3_step(q)==SQLITE_ROW)fprintf(report,"schema=%s\n",sqlite3_column_text(q,1));
    }
done:sqlite3_finalize(q);sqlite3_exec(db,"ROLLBACK",NULL,NULL,NULL);sqlite3_close(db);
}
static void inspect_files(const char *path,const char *title,unsigned depth,unsigned *seen){
    if(depth>4||*seen>=128)return;
    DIR *dir=opendir(path);if(!dir)return;struct dirent *entry;
    while((entry=readdir(dir))&&*seen<128){
        if(!strcmp(entry->d_name,".")||!strcmp(entry->d_name,".."))continue;
        (*seen)++;char full[512];int n=snprintf(full,sizeof(full),"%s/%s",path,entry->d_name);if(n<0||(size_t)n>=sizeof(full))continue;
        int fd=open(full,O_RDONLY|O_NOFOLLOW|O_CLOEXEC|O_NONBLOCK);struct stat s;
        if(fd<0)continue;if(fstat(fd,&s)){close(fd);continue;}
        if(S_ISDIR(s.st_mode)){close(fd);inspect_files(full,title,depth+1,seen);continue;}
        if(!S_ISREG(s.st_mode)){close(fd);continue;}
        unsigned char prefix[16]={0};ssize_t got=pread(fd,prefix,sizeof(prefix),0);
        fprintf(report,"file=%s size=%lld prefix=",entry->d_name,(long long)s.st_size);
        for(int i=0;i<got&&i<8;i++)fprintf(report,"%02x",prefix[i]);fputc('\n',report);
        if(got==16&&!memcmp(prefix,"SQLite format 3",16)){close(fd);inspect_db(full);continue;}
        /* Preserve only bounded trophy binary state for offline format inspection.
         * No SQLite DB, encryption key or arbitrary filesystem contents exported. */
        if((!strcmp(entry->d_name,"TRPTITLE.DAT")||!strcmp(entry->d_name,"TROPUSR.DAT"))&&s.st_size>0&&s.st_size<=2*1024*1024){
            char dest[256];snprintf(dest,sizeof(dest),STAGE "/%s-%s",title,entry->d_name);
            int out=open(dest,O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC,0600);
            if(out>=0){unsigned char bytes[65536];off_t at=0;while(at<s.st_size){size_t want=(size_t)(s.st_size-at);if(want>sizeof(bytes))want=sizeof(bytes);ssize_t k=pread(fd,bytes,want,at);if(k<=0||write(out,bytes,(size_t)k)!=k)break;at+=k;}fsync(out);close(out);}
        }
        close(fd);
    }closedir(dir);
}
static int volume(const char *title){
    if(!title_ok(title)||!same_user())return -1;
    char source[256],copy[256],mount[256],keypath[256];
    snprintf(source,sizeof(source),"/user/home/%08x/trophy/data/%s/trophy.img",selected,title);
    snprintf(keypath,sizeof(keypath),"/user/home/%08x/trophy/data/%s/sealedkey",selected,title);
    snprintf(copy,sizeof(copy),STAGE "/%s.img",title);snprintf(mount,sizeof(mount),STAGE "/%s-mount",title);
    int src=open(source,O_RDONLY|O_NOFOLLOW|O_CLOEXEC),dst=open(copy,O_RDWR|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC,0600);
    if(src<0||dst<0){if(src>=0)close(src);if(dst>=0)close(dst);return -2;}
    int rc=ps4_image_snapshot(src,dst,32*1024*1024);close(src);close(dst);
    fprintf(report,"volume=%s copy_rc=%d\n",title,rc);if(rc)return rc;
    unsigned char keys[132]={0},second[96]={0};int key=open(keypath,O_RDONLY|O_NOFOLLOW|O_CLOEXEC);struct stat ks;
    if(key<0)return -3;
    int valid=!fstat(key,&ks)&&S_ISREG(ks.st_mode)&&ks.st_size==96&&pread(key,keys,96,0)==96&&pread(key,second,96,0)==96&&!memcmp(keys,second,96)&&!memcmp(keys,"pfsSKKey",8);
    close(key);if(!valid){erase(keys,sizeof(keys));erase(second,sizeof(second));return -4;}
    checkpoint("unsealing key in memory; no key output");
    int manager=open("/dev/pfsmgr",O_RDWR|O_CLOEXEC);rc=manager<0?-1:ioctl(manager,0xc0845302UL,keys);if(manager>=0)close(manager);
    fprintf(report,"key_operation_rc=%d errno=%d\n",rc,errno);if(rc){erase(keys,sizeof(keys));erase(second,sizeof(second));return -5;}
    if(!same_user()||mkdir(mount,0700)){erase(keys,sizeof(keys));erase(second,sizeof(second));return -6;}
    MountOpt opt={0};rc=sceFsInitMountTrophyDataOpt(&opt);opt.budgetid="system";
    if(!rc){checkpoint("mounting disposable copy only");rc=sceFsMountTrophyData(&opt,copy,mount,keys+96);}
    erase(keys,sizeof(keys));erase(second,sizeof(second));fprintf(report,"mount_rc=%d\n",rc);fflush(report);
    if(rc<0){rmdir(mount);return rc;}
    unsigned seen=0;inspect_files(mount,title,0,&seen);
    UnmountOpt unmount={0};int end=sceFsInitUmountTrophyDataOpt(&unmount);if(!end)end=sceFsUmountTrophyData(&unmount,mount,rc,0);
    fprintf(report,"unmount_rc=%d\n",end);if(end){checkpoint("copy remains mounted; preserve staging for manual review");return -7;}
    rmdir(mount);unlink(copy);return 0;
}
int main(void){
    if(geteuid()!=0||mkdir(STAGE,0700))return 1;
    int fd=open(STAGE "/report.txt",O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC,0600);if(fd<0)return 2;
    report=fdopen(fd,"w");if(!report){close(fd);return 3;}setvbuf(report,NULL,_IONBF,0);
    checkpoint("PS4 disposable-copy inspection v3; originals never mounted or written; no sync");
    int init=sceUserServiceInitialize(NULL),profile=sceUserServiceGetForegroundUser(&selected);
    fprintf(report,"user_service_init_rc=%d foreground_user_rc=%d\n",init,profile);
    if(profile||selected==UINT32_MAX){checkpoint("foreground profile unavailable");fclose(report);return 6;}
    pid_t me=getpid();uint64_t original=kernel_get_ucred_authid(me);
    unsigned char original_caps[16],temporary_caps[16];memset(temporary_caps,255,sizeof(temporary_caps));
    if(!original||kernel_get_ucred_caps(me,original_caps)||kernel_set_ucred_authid(me,0x4800000000000010ULL)){checkpoint("own-process credential setup failed");fclose(report);return 4;}
    int caps=kernel_set_ucred_caps(me,temporary_caps);fprintf(report,"own_process_caps_setup_rc=%d\n",caps);
    if(caps){kernel_set_ucred_authid(me,original);fclose(report);return 7;}
    int fs=load_fs();fprintf(report,"filesystem_resolution_rc=%d\n",fs);
    char root[128];snprintf(root,sizeof(root),"/user/home/%08x/trophy/data",selected);DIR *dir=fs?NULL:opendir(root);
    if(dir){struct dirent *entry;unsigned count=0;while((entry=readdir(dir))&&count<8){if(!title_ok(entry->d_name))continue;count++;int rc=volume(entry->d_name);fprintf(report,"inspection_rc=%d\n",rc);if(rc==-7)break;}closedir(dir);}
    int restore_caps=kernel_set_ucred_caps(me,original_caps),restore=kernel_set_ucred_authid(me,original);
    fprintf(report,"own_process_caps_restore_rc=%d own_process_authid_restore_rc=%d\n",restore_caps,restore);
    erase(original_caps,sizeof(original_caps));erase(temporary_caps,sizeof(temporary_caps));
    checkpoint("inspection complete");fclose(report);return restore||restore_caps?5:0;
}
