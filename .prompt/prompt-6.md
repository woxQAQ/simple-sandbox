本项目的目的是构建一个安全的代码沙盒用于执行用户提交的代码。目前语言运行时架构如下

```

src\
  runtime\
    common\ # 公共代码
    nodejs\ # nodejs运行时
      plugins\ # nodejs插件
      transformer.js # 插件transformer，将插件逻辑应用到用户代码中
      package.json # transformer 依赖
      runtime.py # nodejs 语言运行时代码
    python\ # python 运行时，逻辑同上
      plugins\
      transformer.py
      runtime.py
    security\ # 安全运行时代码
    utils\
      crypto_utils.py # 代码加密工具库
      entrypoint_templates.py # 运行时执行入口模板生成器代码
```

目前本项目有以下几个问题

- 语言运行时管理混乱，目前几乎处于失灵状态
  - 运行时强依赖于打包结果
  - python 运行时报错没有详细的报错日志
- 日志混乱，有些没必要打印日志的地方打印了日志
- 测试复杂，e2e测试启动服务器，需要通过 docker/Dockerfile.test 打包后启动容器进行测试。

要求你作出以下重构

1. 重构语言运行时，将关键的依赖项配置化，方便测试时进行替换，避免强依赖于构建时
  - 保留当前的插件相关代码,在运行代码之前需要经过 transformer 进行转换
  - 保留当前加密代码，运行时解密和安全策略注入的逻辑
  - 审查日志代码，不要每个步骤都记录日志，只在关键的步骤执行后记录日志
  - 重构 python entrypoint template，使其能抛出完整的报错
  - 简化构建逻辑，修改 docker/ 和 scripts/ 下的代码
2. 重构测试逻辑，要求能在本地模拟出容器沙盒环境，本地测试结果应该与构建后容器内的运行结果保持一致
  - 集成测试实现运行时集成测试和安全集成测试
  - 移除e2e测试

请你你经过深思熟虑后，描述你的计划，并执行重构和运行测试。你不需要保证向后兼容性
