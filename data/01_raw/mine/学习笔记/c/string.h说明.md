---
title: string.h说明
tags: [C语言]
category: 学习
published: 2023-10-29T19:32:42
---

# string.h 说明

## strlen 函数

返回字符串的长度。

```c
size_t strlen(const char*s);  // 返回数组s的长度（不包含末尾的0）
```

## strcmp 函数

用于比较两个字符串。可以比较出两个字符串的大小。

```c
// 返回值：
// s1 == s2  -> 0
// s1 > s2   -> 1
// s1 < s2   -> -1
int strcmp()
```

输出两个不相等字符的差值。

## strcpy 函数

把第二个字符串里的字符拷贝到第一个字符串里，结果返回第一个字符串。

```c
char *strcpy(char* a, char* b);  // 把b拷贝进a里
```

### 复制字符串示例

```c
char *dst = (char*)malloc(strlen(src) + 1);
```

动态申请内存的时候，由于数组的长度最后是有`\0`，所以必须多申请一位。

## strchr 函数

```c
strchr(const char *s, int c);
```

这个函数是用来查找在字符串s里c第一次出现的位置。

例如：

```c
char *a = strchr(s, 't');
```

就是查找在字符串s里t第一次出现的位置，返回的是一个地址。
