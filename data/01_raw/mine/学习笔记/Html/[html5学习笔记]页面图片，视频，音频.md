---
title: "[html5学习笔记]页面图片，视频，音频"
published: 2024-02-24T23:53:01
tags: [Html,Web开发]
category: "学习"
---

# HTML5 页面图片、视频、音频

## 基础概念

- Base 64 也是一种编码形式的图片储存
- MP3 是音频文件
- MP4 是视频文件

> 音视频文件在引入当前页面时，**默认不允许用户控制播放**。

- `loop` 可以设置音频文件是否循环播放

---

## 图片标签

### 基本写法

```html
<img src="图片路径" alt="替代文本">
```

### 常用属性

| 属性 | 说明 |
|------|------|
| `src` | 图片路径 |
| `alt` | 图片加载失败时显示的提示文字 |
| `width` | 图片宽度 |
| `height` | 图片高度 |
| `title` | 鼠标悬停时显示的提示 |

---

## 音频标签

### 基本写法

```html
<audio src="音频路径"></audio>
```

### controls 属性

`controls` 是无需赋值的特殊属性，用于显示播放控件：

```html
<audio controls src="xxx.mp3"></audio>
```

### source 标签

除了用 `src` 控制路径，也可以用 `<source>` 控制文件路径：

```html
<audio controls>
    <source src="xxx.mp3">
</audio>
```

### 兼容提示文字

可以在标签内写提示文字，当音频无法播放时显示：

```html
<audio controls>
    对不起！当前浏览器无法播放这个音频文件。
    <source src="xxx.mp3">
</audio>
```

---

## 多格式兼容

### 为什么要多格式

有的浏览器不支持 MP3，但支持 OGG，可同时提供多种格式：

```html
<audio controls>
    对不起！当前浏览器无法播放这个音频文件。
    <source src="xxx.mp3">
    <source src="xxx.ogg">
</audio>
```

### 工作原理

- HTML 从上往下解析，MP3 播放失败会自动尝试 OGG
- 所有格式都失败时，显示内部提示文本
- 浏览器识别 `<audio>` / `<source>` 则显示播放器；不识别则显示提示文字

---

## 视频标签

### 基本写法

```html
<video src="视频路径"></video>
```

### 常用属性

| 属性 | 说明 |
|------|------|
| `controls` | 显示播放控件 |
| `loop` | 循环播放 |
| `autoplay` | 自动播放 |
| `muted` | 静音播放 |
| `width` | 视频宽度 |
| `height` | 视频高度 |

### 多格式兼容

与音频类似，可以使用 `<source>` 标签提供多种格式：

```html
<video controls>
    对不起！当前浏览器无法播放这个视频文件。
    <source src="xxx.mp4">
    <source src="xxx.webm">
    <source src="xxx.ogg">
</video>
```
