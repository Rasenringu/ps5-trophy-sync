#pragma once
#include <stdint.h>
#include <sys/types.h>
uint64_t kernel_get_ucred_authid(pid_t);
int kernel_set_ucred_authid(pid_t,uint64_t);
int kernel_get_ucred_caps(pid_t,uint8_t*);
int kernel_set_ucred_caps(pid_t,const uint8_t*);
uintptr_t kernel_dynlib_dlsym(int,uint32_t,const char*);
