---
title: "html week 5 学习笔记整理"
published: 2024-02-25T00:17:01
tags: [Html,Web开发, css]
category: "学习"
---

# CSS 基础与选择器学习笔记

## 优先级

**行内样式** > 内部样式 ≈ 外部样式

---

## Link 标签

引入外部 CSS 文件或网页图标：

```html
<link rel="stylesheet" href="styles.css">
<link rel="icon" href="baidu.com">
```

---

## 选择器

### 类选择器

选择指定 class 的元素：

```css
.class {
    属性: 属性值;
}
```

### 基础选择器优先级

**Id 选择器 > 类选择器 > 标签选择器 > 全局选择器**

---

## 后代元素选择器

选择祖先元素的后代元素：

```css
祖先 后代 {
    属性: 属性值;
}
```

**示例**（box 内所有 a）：

```css
.box a {
    font-size: 10px;
}
```

### 子元素选择器

仅子元素生效：

```css
.box > a {
    color: red;
}
```

---

## 兄弟选择器

### 相邻兄弟选择器

选中紧挨着的后一个兄弟：

```css
前一个兄弟 + 后一个兄弟 {
    属性: 属性值;
}
```

### 通用兄弟选择器

选中 A 后所有 b 兄弟：

```css
A ~ b {
    属性: 属性值;
}
```

---

## 并集选择器 & 交集选择器

### 并集选择器

```css
选择器1, 选择器2 {
    /* 样式 */
}
```

### 交集选择器

```css
选择器1选择器2选择器3 {
    /* 样式 */
}
```

---

## 字体样式

| 属性 | 说明 |
|------|------|
| `font-size` | 字体大小 |
| `font-weight` | 字体粗细 |
| `font-family` | 字体，多字体用逗号分隔 |
| `font-style` | 是否斜体 |

> 后代元素会继承父元素样式，自身有样式则不继承。

---

## 颜色表示方式

- **英文单词**：`red`、`black`
- **RGB**：`rgb(0-255, 0-255, 0-255)`
- **十六进制**（最常用）：`#aabbcc`，可简写如 `#fff`
- **RGBA**：带透明度，`rgba(r, g, b, 0-1)`

---

## 文本设置

### text-align

对齐方式：`left` / `center` / `right`

### text-decoration

文本装饰：

| 属性值 | 效果 |
|--------|------|
| `underline` | 下划线 |
| `overline` | 上划线 |
| `none` | 无装饰 |
| `line-through` | 删除线 |

---

## 背景样式

| 属性 | 说明 |
|------|------|
| `background-color` | 背景颜色 |
| `background-image` | 背景图片 |

### 背景图片语法

```css
background-image: url(地址);
```

> 背景图片默认是左上角开始显示，默认会平铺，直到弄满元素位置

### background-repeat

平铺方式：

| 属性值 | 效果 |
|--------|------|
| `repeat` | 默认全平铺 |
| `repeat-x` | X 轴平铺 |
| `repeat-y` | Y 轴平铺 |
| `no-repeat` | 不平铺 |

### 其他背景属性

| 属性 | 说明 |
|------|------|
| `background-size` | 背景大小（宽 高 / cover / contain） |
| `background-position` | 背景位置 |
| `background-attachment` | 背景是否随滚动条滚动 |
