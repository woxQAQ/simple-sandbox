请为我的Code Sandbox项目编写完整的端到端(E2E)测试套件。

# 测试环境

本项目主要采用本地开启docker容器来模拟完整的沙盒环境进行测试。虽然主要考虑的是本地测试，你也要预留出切换api端点的接口。

# 测试架构

遵循本项目的规范，所有的e2e测试代码都放在 tests/e2e 下，以下是e2e测试的大致框架

```
tests/e2e
  common/
    containers.py
    config.py
    client.py
    utils.py
  suites/
    test-python-codes.py
    test-nodejs-codes.py
  .env # 存放e2e测试的环境变量
  .env.example
  e2e.py
  Makefile # 存放用于e2e测试的快捷命令
```

## common/containers.py

由于服务运行在容器环境中，因此我们需要开启容器来进行测试。

在这个文件中，你需要实现一个 `ContainerManager` 类，这个类需要实现

- 创建容器，等待容器就绪，停止/删除容器的容器生命周期管理，基于 `docker`
- 使用 python 的 `contextmanager` 实现资源的创建和释放
- 容器管理是为了本地测试方便的，需要有一个开关来启停

## common/config.py

这个文件存放测试运行所需的所有配置信息，基于 `pydantic`，从环境变量中读取配置信息

你需要至少这些配置信息

- 容器镜像，容器名和容器端口，以及容器管理的开关
- api服务的路径和端口

你不需要以下配置

- 日志配置，直接写死即可

## common/client.py

这个文件你需要实现一个与沙盒服务器交互的http客户端

## common/utils.py

这个文件存放一些测试所需要的通用的工具函数。注意，你不要把一些不相关的函数组合在一起形成一个 `TestUitl` 类

## suites/test-{lang}-code.py

这些文件存放的是测试各个语言的运行时功能的具体测试用例

- 这些文件都需要测试正常的无风险代码和含有危险系统调用的代码
- python 的测试用例需要额外测试python语言插件
- 不需要太多用例

## .env 和 .env.example

测试时的环境变量,.env 是具体的环境变量文件，但是会被 git 忽略，.env.example作为示例

## makefile

make 文件，你只需要以下内容

- 运行e2e测试的快速命令

## e2e.py

e2e 测试的入口文件，你需要实现测试的入口和测试结果的归纳和产出报告

# 注意事项

- 请你严格遵循上述的文件框架和各文件的作用，在此框架基础上，你可以适当扩展你的逻辑
- 当你需要安装任何依赖时，请你使用 `uv add <pkg> --dev` 安装到 dev group 中
- 请你参考python编写测试的最佳实践
- 最后请你输出一份e2e的测试报告，内容包括插件逻辑的测试结果，危险调用的测试结果等
- 请你不要在本地开启服务器来进行测试
- 我们只需要能够运行完整的 e2e 测试，不需要其他入口。
