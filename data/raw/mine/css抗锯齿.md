---
title: CSS transform旋转的锯齿效果解决办法
tags: [博客文章, Web开发]
category: 开发日志
published: 2024-11-07T20:16:01
---

在完成web开发作业的时候，需要写一个旋转的input，但写完后，input的外边框发生了明显的锯齿效果，如下：

解决办法：

利用css3d会使用gpu加速渲染的特性，给div增加3d样式，即在z轴旋转0°，从而使用gpu精确渲染来解决这个问题：

```css
        div{
            transform:rotate(-7deg) translateZ(0);
            transform:rotate(-7deg);
            margin-top: 10px;
        }
```

如果你直到抗锯齿的原理，即利用渐变色过渡来达到较好的视觉效果，那么使用css滤镜也是一个不错的办法：

```css
        div{
            transform:rotate(-7deg); 
            filter: blur(0.1px); 
            margin-top: 10px;
        }
```