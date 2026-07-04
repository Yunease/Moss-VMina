---
title: css编写位置
tags: [css]
category: 学习
published: 2023-12-02T14:15:48
---

# CSS 编写位置

## 一、行内样式（内联样式）

- 只能对一个标签生效
- 样式发生变化后需要一个一个改
- 不方便维护和修改

## 二、内部样式表

将样式写在 `head` 标签下的 `style` 标签里。

### 示例代码

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="这是一个网页">
    <meta name="title" content="砂铃的网页">
    <title>the_love</title>
    <style>
        p{color:bisque; font-size: larger;}
    </style>
</head>
<body>
    <p>我爱你！</p>
</body>
</html>
```

### 基本语法

```css
标签名 {
    样式
}
```

### 优点

- 可以通过 CSS 选择器设置不同的样式

### 缺点

- 不能跨页面使用

## 三、外部样式表（推荐）

将 CSS 样式编写到一个外部的 `.css` 文件中。

### 使用步骤

1. 创建 `.css` 文件
2. 通过 `link` 标签引入 HTML 文件
3. `link` 标签需要写在 `head` 标签下

```html
<link rel="stylesheet" href="style.css">
```

### 优点

- 可以在不同页面复用
- 外部 CSS 文件会被缓存到本地，加快网页访问速度
- **开发中最常用的方式**

## CSS 注释

```css
/* 这里是注释 */
```

> 注释的快捷键：`Ctrl + /`
