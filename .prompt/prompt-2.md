关于运行时的一些问题：

1. docker/seccomp.json 在 docker-compose 使用。这里 seccomp 是在容器层面取限制了,是否在运行时去使用 seccomp 更合适？
2. 原先的拓展机制，在 *_transformers 中编写字符串并在实际运行之前运行其中的代码。然而代码全部编码在字符串中，后续拓展会导致代码可读性极差,请你考虑一种新的设计
