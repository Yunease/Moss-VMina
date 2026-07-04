---
title: 插叙：进程api
tags: [操作系统]
category: 学习
published: 2024-10-09T14:39:14
---

# 插叙：进程API

## 关键问题

如何创建并控制进程？

## Fork() 系统调用

系统调用fork用于创建新的进程，新创建的进程几乎和原有进程一样，但不再执行前面的语句块，而是执行fork之后的语句块，用代码表示如下：

```c
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

int main(int argc, char *argv[])
{
    printf("hello world (pid:%d)\n", (int) getpid());
    int rc = fork();
    if (rc < 0) { // fork failed; exit
        fprintf(stderr, "fork failed\n");
        exit(1);
    } else if (rc == 0) { // child (new process)
        printf("hello, I am child (pid:%d)\n", (int) getpid());
    } else { // parent goes down this path (main)
        printf("hello, I am parent of %d (pid:%d)\n", rc, (int) getpid());
    }
    return 0;
}
```

> 运行结果只有一个hello输出

## 子进程特性

子进程不是完全拷贝了父进程，它也拥有自己的私有内存，寄存器和程序计数器，但fork返回的值是不同的（是的，fork需要返回一个int类型的参数，所以你需要用一个变量来储存它！），父进程返回的值是创建子进程的pid，而子进程获得的返回值是0。

## Wait()系统调用

有些时候，我们需要从父进程里创建一个子进程，并且在子进程执行完毕后才会继续执行父进程并退出，这很重要，因此我们使用wait系统调用。

## Exec进程

这个系统调用可以让子进程执行与父进程不同的程序。例如，在p2.c 中调用 fork()，这只是在你想运行相同程序拷贝时有用。但是我们常常想运行不同的程序，exec()正好做这样的事。

## 其他API

多读man手册，这是成为一个程序员的必经之路。

除了fork、exec、wait之外，unix还提供了许多同其他交互的进程方式，例如kill系统调用向进程发送信号要求睡眠或终止…
