#!/usr/bin/env nu

# 关闭 command 为 tmp/sandboxd 的进程
# Kill processes with command "tmp/sandboxd"

def main [] {
    print "正在查找 command 为 sandboxd 的进程..."

    # 使用 ps 命令查找包含 tmp/sandboxd 的进程
    let processes = (ps | where name =~ "sandboxd")

    if ($processes | length) == 0 {
        print "✓ 没有找到 command 为 sandboxd 的进程"
        return
    }

    print $"找到 ($processes | length) 个匹配的进程:"

    # 显示找到的进程信息
    for process in $processes {
        print $"  - PID: ($process.pid) | Command: ($process.name)"
    }

    # 逐个终止进程
    for process in $processes {
        let pid = $process.pid
        print $"正在终止进程 PID: ($pid)"

        try {
            # 先尝试优雅终止 (SIGTERM)
            kill $pid
            print $"✓ 进程 ($pid) 已终止"
        } catch {
            print $"⚠️ 进程 ($pid) 终止失败，尝试强制终止 (SIGKILL)..."
            try {
                kill -9 $pid
                print $"✓ 进程 ($pid) 已强制终止"
            } catch {
                print $"✗ 强制终止进程 ($pid) 失败，可能需要手动处理"
            }
        }
    }

    # 验证进程是否已终止
    print "验证进程终止状态..."
    let remaining_processes = (ps | where name =~ "sandboxd")

    if ($remaining_processes | length) == 0 {
        print "✓ 所有 tmp/sandboxd 进程已成功终止"
    } else {
        print $"⚠️ 还有 ($remaining_processes | length) 个 tmp/sandboxd 进程未终止:"
        for process in $remaining_processes {
            print $"  - PID: ($process.pid) | Command: ($process.command)"
        }
        print "请手动检查并终止这些进程"
    }
}
