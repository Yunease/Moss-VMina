---
title: typedef的用法
tags: [C语言]
category: 学习
published: 2023-11-23T13:03:11
---

# typedef的用法

## 基本概念

typedef关键字的作用：起别名，方便。

### 基本用法

例如：

```c
typedef int nmsl;
nmsl a;  // 在这之后的nmsl就和int同样效果了
a = 1;
```

可以给类型起别名。

它的使用规范是：

```
typedef + 类型 + 别名
```

效果就是使用别名和原类型有同样的效果。

## typedef的优点

typedef的优点就在于可以批处理变量。

比如我们定义了100个int变量，如果想要转化成char变量就需要改100次，如果使用typedef就只需要一次修改。

## 结构体应用

可以这样改善程序的可读性：

```c
typedef struct Adata{
    int month;
    int day;
    int year;
}data;
```

这样以后就可以用data来代替struct Adata使用了，比如说我们想规定一个变量x是名为adata的结构体类型，我们就可以这么写：

```c
data x;
```

果然，很方便吧！
