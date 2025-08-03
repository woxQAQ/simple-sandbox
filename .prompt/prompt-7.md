我们正在开发一个安全地运行用户提交的不可信代码的代码沙盒，整个代码沙盒会
暴露一个 http route 来提供服务
我们使用运行时动态注入 seccomp 规则 + 文件系统隔离的策略保证安全
请你在经过认真思考，统筹整个代码仓库的前提下，对代码运行时作出以下重构

1. 保持当前 seccomp lib 位于 /var/sandbox/{lang} 的设计。
2. python 运行时运行在 /var/sandbox/python 目录下，entrypoint 文件应该存放在/var/sandbox/python/tmp/entrypoint-[uuid].py 下
3. python 运行时会 chroot 到 /var/sandbox/python 下，因此你需要复制完整的 python 运行时，包括 /usr/local/lib/python-{python-version} 和其他网络相关的文件。详细请参考 @scripts/env.py，python 语言的这个步骤在构建时处理即可
4. nodejs 由于其特殊性，如果复用旧的 nodejs 依赖可能会导致安全问题。因此 nodejs 运行时需要运行在 /tmp/sandbox-[uuid], 你需要在这个目录下复制 /var/sandbox/nodejs 下的安全库以及上述的网络相关的文件，这个操作应该是每次创建nodejs沙盒环境的沙盒运行
5. 基于 4. 当前的 transformer 也会有风险，请你移除 nodejs transformer 相关的代码，nodejs不支持插件
