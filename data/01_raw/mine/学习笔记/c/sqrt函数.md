---
title: sqrt函数
tags: [C语言]
category: 学习
published: 2023-10-13T20:14:32
---

# sqrt函数

## 函数说明

Sqrt函数在使用时需要包含头文件math.h，也就是这样：

```c
#include <math.h>
```

Sqrt函数的用途是求出一个非负数的平方根，写作这样：

```c
sqrt(n);
```

## 注意事项

唯一需要注意的地方是，sqrt返回的是一个double形的变量，所以如果用%d来输出的话就会出错。

就算想要只保留整数，也应该经过强制转换：

```c
(int)a
```
