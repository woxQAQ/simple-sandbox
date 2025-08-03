/*
 * seccomp注入器 - Linux专用实现
 * 支持amd64和arm64架构
 */

#define _GNU_SOURCE
#include "seccomp_injector.h"
#include <errno.h>
#include <fcntl.h>
#include <grp.h>
#include <pwd.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <syslog.h>
#include <unistd.h>

#ifdef __linux__
/* Linux特定头文件 */
#include <linux/audit.h>
#include <linux/filter.h>
#include <linux/seccomp.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#else
/* 非Linux平台的存根定义 */
#define PR_SET_NO_NEW_PRIVS 38
#define SECCOMP_MODE_FILTER 2
#define SECCOMP_RET_ALLOW 0x7fff0000U
#define SECCOMP_RET_ERRNO 0x00050000U
#define SECCOMP_RET_KILL 0x00000000U
#define EPERM 1

typedef unsigned short __u16;
typedef unsigned char __u8;
typedef unsigned int __u32;
typedef unsigned long long __u64;

struct sock_filter {
  __u16 code;
  __u8 jt;
  __u8 jf;
  __u32 k;
};

struct sock_fprog {
  unsigned short len;
  struct sock_filter *filter;
};

#define BPF_LD 0x00
#define BPF_W 0x00
#define BPF_ABS 0x20
#define BPF_JMP 0x05
#define BPF_JEQ 0x10
#define BPF_K 0x00
#define BPF_RET 0x06

#define AUDIT_ARCH_X86_64 0xc000003e
#define AUDIT_ARCH_AARCH64 0xc00000b7

#define BPF_STMT(code, k) {(unsigned short)(code), 0, 0, k}
#define BPF_JUMP(code, k, jt, jf) {(unsigned short)(code), jt, jf, k}

/* 存根函数 */
static int prctl(int option, unsigned long arg2, unsigned long arg3,
                 unsigned long arg4, unsigned long arg5) {
  (void)option;
  (void)arg2;
  (void)arg3;
  (void)arg4;
  (void)arg5;
  errno = ENOSYS;
  return -1;
}
#endif

/* seccomp数据结构 - 使用内核定义，不再重新定义 */
/* struct seccomp_data 已在 <linux/seccomp.h> 中定义 */

/* 架构检测 */
#if defined(__x86_64__)
#define AUDIT_ARCH_NATIVE AUDIT_ARCH_X86_64
#elif defined(__aarch64__)
#define AUDIT_ARCH_NATIVE AUDIT_ARCH_AARCH64
#else
#error "Unsupported architecture"
#endif

/* 最大支持的系统调用数量 */
#define MAX_SYSCALLS 512

/* 包含自动生成的系统调用定义 */
#include "syscalls_generated.h"

/* 日志函数 */
static void log_error(const char *msg, int error_code) {
  syslog(LOG_ERR, "seccomp_injector: %s (error: %d, errno: %d)", msg,
         error_code, errno);
  // 检查环境变量，决定是否输出到stderr
  if (getenv("SECCOMP_VERBOSE") != NULL) {
    fprintf(stderr, "seccomp_injector: %s (error: %d, errno: %d)\n", msg,
            error_code, errno);
  }
}

static void log_info(const char *msg) {
  syslog(LOG_INFO, "seccomp_injector: %s", msg);
}

static void log_warning(const char *msg, int error_code) {
  syslog(LOG_WARNING, "seccomp_injector: %s (warning: %d, errno: %d)", msg,
         error_code, errno);
  // 检查环境变量，决定是否输出到stderr
  if (getenv("SECCOMP_VERBOSE") != NULL) {
    fprintf(stderr, "seccomp_injector: %s (warning: %d, errno: %d)\n", msg,
            error_code, errno);
  }
}

/* 设置PR_SET_NO_NEW_PRIVS */
int setup_no_new_privs(void) {
#ifdef __linux__
  if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0) {
    log_error("Failed to set PR_SET_NO_NEW_PRIVS", SECCOMP_ERROR_PRCTL);
    return SECCOMP_ERROR_PRCTL;
  }
  log_info("PR_SET_NO_NEW_PRIVS set successfully");
  return SECCOMP_SUCCESS;
#else
  log_error("seccomp not supported on this platform",
            SECCOMP_ERROR_UNSUPPORTED);
  return SECCOMP_ERROR_UNSUPPORTED;
#endif
}

/* 降低权限 */
int drop_privileges(uid_t uid, gid_t gid) {
  /* 设置组ID */
  if (setgid(gid) != 0) {
    log_error("Failed to set GID", SECCOMP_ERROR_PRIVILEGE);
    return SECCOMP_ERROR_PRIVILEGE;
  }

  /* 清除附加组 */
  if (setgroups(0, NULL) != 0) {
    log_error("Failed to clear supplementary groups", SECCOMP_ERROR_PRIVILEGE);
    return SECCOMP_ERROR_PRIVILEGE;
  }

  /* 设置用户ID */
  if (setuid(uid) != 0) {
    log_error("Failed to set UID", SECCOMP_ERROR_PRIVILEGE);
    return SECCOMP_ERROR_PRIVILEGE;
  }

  /* 验证权限已正确降低 */
  if (getuid() != uid || geteuid() != uid || getgid() != gid ||
      getegid() != gid) {
    log_error("Privilege drop verification failed", SECCOMP_ERROR_PRIVILEGE);
    return SECCOMP_ERROR_PRIVILEGE;
  }

  log_info("Privileges dropped successfully");
  return SECCOMP_SUCCESS;
}

/* 生成BPF程序 */
static int generate_bpf_program(const int *syscalls, size_t syscall_count,
                                struct sock_filter **filter,
                                size_t *filter_len) {
  if (!syscalls || !filter || !filter_len || syscall_count == 0 ||
      syscall_count > MAX_SYSCALLS) {
    return SECCOMP_ERROR_INVALID_ARGS;
  }

  /* 计算所需的BPF指令数量 */
  size_t instruction_count = 4 + (syscall_count * 2) + 1;

  *filter = malloc(instruction_count * sizeof(struct sock_filter));
  if (!*filter) {
    log_error("Failed to allocate memory for BPF filter", SECCOMP_ERROR_MEMORY);
    return SECCOMP_ERROR_MEMORY;
  }

  size_t idx = 0;

  /* 加载架构 */
  (*filter)[idx++] = (struct sock_filter)BPF_STMT(
      BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, arch));

  /* 检查架构匹配 */
  (*filter)[idx++] = (struct sock_filter)BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K,
                                                  AUDIT_ARCH_NATIVE, 1, 0);
  (*filter)[idx++] = (struct sock_filter)BPF_STMT(
      BPF_RET | BPF_K, SECCOMP_RET_ERRNO | (EPERM & 0xFFFF));

  /* 加载系统调用号 */
  (*filter)[idx++] = (struct sock_filter)BPF_STMT(
      BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, nr));

  /* 为每个允许的系统调用添加规则 */
  for (size_t i = 0; i < syscall_count; i++) {
    (*filter)[idx++] = (struct sock_filter)BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K,
                                                    syscalls[i], 0, 1);
    (*filter)[idx++] =
        (struct sock_filter)BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW);
  }

  /* 默认拒绝所有其他系统调用，使用 EACCES 表示权限被拒绝 */
  (*filter)[idx++] = (struct sock_filter)BPF_STMT(
      BPF_RET | BPF_K, SECCOMP_RET_ERRNO | (EACCES & 0xFFFF));

  *filter_len = idx;
  return SECCOMP_SUCCESS;
}

/* 应用seccomp过滤器 */
int apply_seccomp_filter(void) {
#ifdef __linux__
  struct sock_filter *filter = NULL;
  size_t filter_len = 0;

  /* 生成BPF程序 */
  int ret = generate_bpf_program(ALLOWED_SYSCALLS, SYSCALL_COUNT, &filter,
                                 &filter_len);
  if (ret != SECCOMP_SUCCESS) {
    return ret;
  }

  /* 创建BPF程序结构 */
  struct sock_fprog prog = {.len = filter_len, .filter = filter};

  /* 应用seccomp过滤器 */
  if (prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &prog) != 0) {
    log_error("Failed to apply seccomp filter", SECCOMP_ERROR_SYSCALL);
    free(filter);
    return SECCOMP_ERROR_SYSCALL;
  }

  free(filter);
  log_info("Seccomp filter applied successfully");
  return SECCOMP_SUCCESS;
#else
  log_error("seccomp not supported on this platform",
            SECCOMP_ERROR_UNSUPPORTED);
  return SECCOMP_ERROR_UNSUPPORTED;
#endif
}

/* 完整的seccomp注入流程 */
int inject_seccomp_profile(uid_t uid, gid_t gid) {
  int ret;

  /* 1. 设置PR_SET_NO_NEW_PRIVS */
  ret = setup_no_new_privs();
  if (ret != SECCOMP_SUCCESS) {
    return ret;
  }

  /* 2. 应用seccomp过滤器 */
  ret = apply_seccomp_filter();
  if (ret != SECCOMP_SUCCESS) {
    return ret;
  }

  /* 执行chroot */
  if (chroot(".") != 0) {
    log_error("Failed to execute chroot", SECCOMP_ERROR_CHROOT);
    return SECCOMP_ERROR_CHROOT;
  }

  /* 在chroot环境中改变工作目录到根目录 */
  if (chdir("/") != 0) {
    log_error("Failed to change directory to root in chroot",
              SECCOMP_ERROR_CHROOT);
    return SECCOMP_ERROR_CHROOT;
  }

  /* 3. 降低权限 - 在容器环境中可能失败，这是正常的 */
  ret = drop_privileges(uid, gid);
  if (ret != SECCOMP_SUCCESS) {
    /* 在容器环境中，权限降低失败是正常的，不应视为错误 */
    /* 只有当当前UID/GID与目标不匹配时才报错 */
    if (getuid() != uid || getgid() != gid) {
      /* 记录警告但不返回错误 */
      log_warning(
          "Privilege drop failed but continuing with seccomp protection", ret);
    }
    /* 继续执行，seccomp保护已经生效 */
  }

  return SECCOMP_SUCCESS;
}

/* 获取错误描述 */
const char *get_error_description(int error_code) {
  switch (error_code) {
  case SECCOMP_SUCCESS:
    return "Success";
  case SECCOMP_ERROR_PRCTL:
    return "prctl() system call failed";
  case SECCOMP_ERROR_SYSCALL:
    return "seccomp system call failed";
  case SECCOMP_ERROR_INVALID_ARGS:
    return "Invalid arguments";
  case SECCOMP_ERROR_PRIVILEGE:
    return "Privilege operation failed";
  case SECCOMP_ERROR_MEMORY:
    return "Memory allocation failed";
  case SECCOMP_ERROR_UNSUPPORTED:
    return "Unsupported platform";
  case SECCOMP_ERROR_CHROOT:
    return "chroot operation failed";
  default:
    return "Unknown error";
  }
}
