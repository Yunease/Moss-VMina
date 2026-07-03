---
title: 利用CSS实现前端背景图片切割
tags: [博客文章, css]
description: '可以看到，这里使用了一个行内空标签，然后设置了行内的style样式，只需要点开background里的url，就可以看到背景图片了。如果只是这么简单的事情，我是不会写这篇文章的。当你点击链接访问进去，会发现原图其实是一堆护符的整图。如果你接触过unity2d开发，一定知道贴图集切割精灵实现图片转化为行动动画的功能。'
published: 2024-10-30T15:38:01
---

最近我在查找wiki的时候看到了这样有趣的东西：

![img](https://i-blog.csdnimg.cn/direct/8e5595aafd17441eb8a5d91f6aea8070.png)![点击并拖拽以移动](data:image/gif;base64,R0lGODlhAQABAPABAP///wAAACH5BAEKAAAALAAAAAABAAEAAAICRAEAOw==)编辑

右侧的空洞骑士护符居然不能选中，周围的文本都是可以复制的，我对此十分感兴趣，因此利用元素定位找到了这个图片的位置：

![img](https://i-blog.csdnimg.cn/direct/d165160f56784f719ecb89cf346d4940.png)![点击并拖拽以移动](data:image/gif;base64,R0lGODlhAQABAPABAP///wAAACH5BAEKAAAALAAAAAABAAEAAAICRAEAOw==)编辑

可以看到，这里使用了一个行内空标签，然后设置了行内的style样式，只需要点开background里的url，就可以看到背景图片了。

如果只是这么简单的事情，我是不会写这篇文章的。

当你点击链接访问进去，会发现原图其实是一堆护符的整图。如果你接触过unity2d开发，一定知道贴图集切割精灵实现图片转化为行动动画的功能。

![img](https://i-blog.csdnimg.cn/direct/e022e3bb2374422cac27ab2e5eeb43ba.png)![点击并拖拽以移动](data:image/gif;base64,R0lGODlhAQABAPABAP///wAAACH5BAEKAAAALAAAAAABAAEAAAICRAEAOw==)编辑

回过头来，我们再来看一下这个css代码块：（这里把style写进了p标签，只作展示）

```css
p{
    display:inline-block;
    vertical-align:middle;
    width:150px;
    height:150px;
    background:url(https://huiji-public.huijistatic.com/hkss/uploads/1/13/HK_Charms_Sprite.png)
    -900px -300px/1350px 900px;
}
```

![点击并拖拽以移动](data:image/gif;base64,R0lGODlhAQABAPABAP///wAAACH5BAEKAAAALAAAAAABAAEAAAICRAEAOw==)

前面的样式主要是设置图片的位置和大小的，我们不做多分析。background属性的最后设置了两串像素格式。

第一串是-900px -300px，这意味着图片显示区域向左移动900px，向上移动300px。后一串数字则是背景显示的大小，如果保存图片，你会发现原图的大小就是1350px/900px：

![img](https://i-blog.csdnimg.cn/direct/e325b29bf71c4d2882e5ebc41bc5f270.png)![点击并拖拽以移动](data:image/gif;base64,R0lGODlhAQABAPABAP///wAAACH5BAEKAAAALAAAAAABAAEAAAICRAEAOw==)编辑



### 有什么用？

在wiki这种多页面的网站里节约资源是很重要的事情，如果一张需要重复多次使用的图片只保存一次，然后在使用的网站利用css切割定位来实现图片的展示，这样可以让一张图重复利用，而且实现也并不需要其他插件，十分方便。
