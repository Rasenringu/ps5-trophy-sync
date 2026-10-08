/* Conspicuously synthetic API responses; never console evidence. */
#include <stdint.h>
uint32_t kernel_get_fw_version(void) { return 0x08000000; }
int kernel_get_ucred_caps(int pid, unsigned char caps[16]) { (void)pid; (void)caps; return -1; }
int sceUserServiceInitialize(void *p) { (void)p; return 0; }
int sceUserServiceTerminate(void) { return 0; }
int sceUserServiceGetForegroundUser(uint32_t *p) { *p = 0x12345678; return 0; }
int sceUserServiceGetLoginUserIdList(int ids[4]) { ids[0]=0x12345678;ids[1]=0x456789ab;ids[2]=-1;ids[3]=-1;return 0; }
