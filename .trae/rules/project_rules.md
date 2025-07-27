# overall instruction

- 请你在实现一个任务过后，不要生成用于演示的example代码和readme文件，除非这个任务本身就是要让你实现example和撰写文档的。
- 测试代码放到 test 目录下
- 不要吃后悔药，即写了一个版本的代码过后，由于功能不符合或者其他的原因又创建一个版本的代码。写代码前需要深思熟虑，如果没办法决定的情况下，你需要进行进一步的思考。如果原来的版本有任何问题，你需要进行修复，而不是创建一个新的版本。如果实在需要创建一个新版本，你要删除掉没有用的旧版本代码

# project instruction

这个项目是一个代码沙盒的实现，项目的主要功能包括：

1. 提供一个安全的环境，让用户在其中运行未知的代码，而不会影响到主机系统。
2. 基于 seccomp 提供系统调用级别的过滤，使用 chroot 和 tempfile 提供文件系统隔离，代码沙盒会被打包为 docker 镜像，使用 docker/k8s 级别的资源限制。
3. 提供一个 API 接口，让用户可以通过 API 接口来运行不可信代码
4. 语言运行时提供插件接口，支持用户自定义某些代码库的逻辑。

项目结构

```
src/
    api/ # fastapi 接口
    security/ # 安全相关的代码
    runtime/ # 不同语言的runtime
        {lang}_runtime.py # 语言运行时
        manager.py # 运行时管理器
        extensions/
            transformers/ # 插件转换器
            plugins/ # 插件代码
tests/ # 测试代码
```

# workflow

## build

构建时需要将设定好的系统调用过滤表编译成动态链接库，动态链接库需要输出到 src/runtime 目录下，语言运行时需要加载这个动态链接库来应用 seccomp 安全策略。