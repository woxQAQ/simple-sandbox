/*
 * seccomp注入器头文件
 * 定义接口和常量
 */

#ifndef SECCOMP_INJECTOR_H
#define SECCOMP_INJECTOR_H

#include <sys/types.h>

/* 错误码定义 */
#define SECCOMP_SUCCESS 0
#define SECCOMP_ERROR_PRCTL -1
#define SECCOMP_ERROR_SYSCALL -2
#define SECCOMP_ERROR_INVALID_ARGS -3
#define SECCOMP_ERROR_PRIVILEGE -4
#define SECCOMP_ERROR_MEMORY -5
#define SECCOMP_ERROR_UNSUPPORTED -6

/* 函数声明 */
#ifdef __cplusplus
extern "C" {
#endif

/**
 * 设置PR_SET_NO_NEW_PRIVS
 * @return 成功返回SECCOMP_SUCCESS，失败返回错误码
 */
int setup_no_new_privs(void);

/**
 * 降低进程权限
 * @param uid 目标用户ID
 * @param gid 目标组ID
 * @return 成功返回SECCOMP_SUCCESS，失败返回错误码
 */
int drop_privileges(uid_t uid, gid_t gid);

/**
 * 应用seccomp过滤器
 * @param syscalls 允许的系统调用号数组
 * @param syscall_count 系统调用数量
 * @return 成功返回SECCOMP_SUCCESS，失败返回错误码
 */
int apply_seccomp_filter(const int* syscalls, size_t syscall_count);

/**
 * 完整的seccomp注入流程
 * @param syscalls 允许的系统调用号数组
 * @param syscall_count 系统调用数量
 * @param uid 目标用户ID
 * @param gid 目标组ID
 * @return 成功返回SECCOMP_SUCCESS，失败返回错误码
 */
int inject_seccomp_profile(const int* syscalls, size_t syscall_count, uid_t uid, gid_t gid);

/**
 * 获取错误描述
 * @param error_code 错误码
 * @return 错误描述字符串
 */
const char* get_error_description(int error_code);

#ifdef __cplusplus
}
#endif

#endif /* SECCOMP_INJECTOR_H */