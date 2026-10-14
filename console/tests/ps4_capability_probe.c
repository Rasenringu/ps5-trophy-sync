/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Capability lookup only. No mount/unmount, sealed-key decryption, database
 * reads/writes, trophy initialization/registration/unlock or network imports. */
#include <dlfcn.h>
#include <fcntl.h>
#include <stdio.h>
#include <sys/stat.h>
#include <unistd.h>
int __patch_init(void){return 0;}
static void inspect(FILE *report,const char *path,const char *const *symbols){
    fprintf(report,"loading=%s\n",path);
    fflush(report);fsync(fileno(report));
    void *module=dlopen(path,RTLD_NOW|RTLD_LOCAL);
    fprintf(report,"module=%s loaded=%d\n",path,module!=NULL);
    if(!module)return;
    for(unsigned i=0;symbols[i];i++){
        fprintf(report,"checking=%s\n",symbols[i]);
        fflush(report);fsync(fileno(report));
        fprintf(report,"export=%s available=%d\n",symbols[i],dlsym(module,symbols[i])!=NULL);
    }
    fputs("closing module\n",report);fflush(report);fsync(fileno(report));
    dlclose(module);
}
int main(void){
    if(geteuid()!=0)return 1;
    int fd=open("/data/trophy-sync-ps4-capabilities.txt",O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC,0600);
    if(fd<0)return 2;struct stat st;
    if(fstat(fd,&st)||!S_ISREG(st.st_mode)||st.st_uid!=geteuid()||(st.st_mode&077)!=0){close(fd);return 3;}
    FILE *report=fdopen(fd,"w");if(!report){close(fd);return 4;}
    if(setvbuf(report,NULL,_IONBF,0)){fclose(report);return 6;}
    const char *fs[]={"sceFsInitMountSaveDataOpt","sceFsMountSaveData","sceFsMountSaveDataReadOnly","sceFsInitUmountSaveDataOpt","sceFsUmountSaveData",NULL};
    const char *trophy[]={"sceNpTrophySystemGetTrophyData","sceNpTrophySystemGetTitleData","sceNpTrophySystemGetTrophyInfo","sceNpTrophySystemGetTitleInfo","sceNpTrophySystemGetTrophyDetails","sceNpTrophySystemGetLocalTrophySummary","sceNpTrophySystemGetTitleFileEntryInfo","sceNpTrophySystemGetNextTitleFileEntryStatus",NULL};
    fputs("TrophySync PS4 export probe v2\nNo trophy APIs called; no images mounted; no credentials or profile identifiers read.\n",report);
    fflush(report);fsync(fd);
    inspect(report,"/system/priv/lib/libSceFsInternalForVsh.sprx",fs);
    inspect(report,"/system/common/lib/libSceNpTrophy.sprx",trophy);
    int ok=!ferror(report)&&!fflush(report)&&!fsync(fd);fclose(report);return ok?0:5;
}
