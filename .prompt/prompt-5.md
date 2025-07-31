本代码沙盒旨在让不可信的代码在安全的地方运行，然而，当前系统的文件系统管理比较混乱

1. 构建时，将 python 和 nodejs 的可执行文件放在 /opt 下，这点没有问题。安全共享库被编译到 /build/lib 下
2. 对于python代码，经过 pip install 后，可以在任意位置运行含有该依赖的代码。
3. 对于nodejs，则必须将依赖复制到代码执行目录下，才可以运行含有依赖的代码。
4. 当前的代码没有经过加密，代码需要通过加密后才能放到文件系统中，并且运行时要能进行解密。

请你综合考虑dockerfile和运行时代码，经过深度思考后，作出以下重构

1. 整个运行时的流程是，应用插件，加密，执行共享库。
2. /var/sandbox/{lang} 是我们存放运行时库的地方，在构建时进行以下操作
  - python依赖一些运行时库，需要复制到 /var/sandbox/python,在运行时要传递给python进程，以下是运行库的路径
    - "/usr/local/lib/python3.10",
	- "/usr/lib/python3.10",
	- "/usr/lib/python3",
	- "/usr/lib/x86_64-linux-gnu",
  - 由于目前nodejs运行时没有使用到依赖库，因此nodejs不需要复制。
  - nodejs和python都需要一些网络依赖，都需要复制到 /var/sandbox/{lang} 下
    - "/etc/ssl/certs/ca-certificates.crt",
	- "/etc/nsswitch.conf",
	- "/etc/resolv.conf",
	- "/run/systemd/resolve/stub-resolv.conf",
	- "/etc/hosts"
3. 需要修改 @scripts/build.sh 使其编译获得的各语言安全共享库拷贝到 /var/sandbox/{lang}下
4. 复制要遵循以下规则
    - 递归处理所有子目录，保持完整的目录结构
    - 针对不同文件类型，使用不同复制逻辑
      - 符号链接直接复制链接关系
      - 设备文件，复制并修改权限为只读
      - 否则，创建硬链接，并保持权限为只读
5. 在运行时对用户代码进行加密，创建 entrypoint.{suffix}，里面的逻辑是接受命令行参数获得解密key，使用key对用户代码进行解密并执行
6. 所有的用户代码都需要放在 /tmp 目录下，用完即删。
