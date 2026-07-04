---
title: sizeof使用
tags: [C语言]
category: 学习
published: 2023-10-08T19:34:13
---

# sizeof使用

## 基本用法

sizeof可以注明使用了多少个字节。

使用方法：

```c
sizeof(int)  // 表明int在内存里占据了多少字节
sizeof(i)    // 表明了变量i在内存里占据了多少字节
```

sizeof是一个静态运算符，在编译完之后就固定了。

## 数据类型字节数

### 常见数据类型

- char：1个字节
- int：4个字节
- short：2个字节（取决于cpu和编译器）
- long：8个字节（取决于cpu和编译器）
- long long：8个字节

### 原理说明

在cpu中，reg是（32/64）位（bit）决定了int的大小。
