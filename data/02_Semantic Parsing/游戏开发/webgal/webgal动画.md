---
title: 一篇文章彻底讲懂Webgal中的自定义动画编写 | webgal动画教程
tags: [博客文章]
category: '开发日志'
published: 2025-12-27T16:17:01
---

## 1.为什么要编写自定义动画

大家好，这里是小琴。今天来讲webgal自定义动画的编写。

可能会有人好奇，为什么要编写自定义动画呢，为什么不用预设好的动画？

这个问题其实很好回答，很多时候我们需要覆盖掉引擎自带的默认动画，而覆盖的方式只能是写一个新的动画，或者诸如CG的平移预览等也需要我们根据实际情况自己编写动画。

废话不多说，我们开始吧。



## 2.自定义动画的关键字

webgal提供了自定义动画的关键字，只需要设置好每个关键帧的动画效果，就能按照线性效果播放。以下关键字复制于webgal的官方文档：

| 属性名         | 释义                                 |
| -------------- | ------------------------------------ |
| alpha          | 透明度，范围0-1                      |
| scale          | 缩放                                 |
| position       | 位置偏移                             |
| rotation       | 旋转角度，单位为弧度                 |
| blur           | 高斯模糊半径                         |
| brightness     | 调节亮度                             |
| contrast       | 调节对比度                           |
| saturation     | 调节饱和度                           |
| gamma          | 调节伽马值                           |
| colorRed       | 颜色分量:红色, 范围0-255             |
| colorGreen     | 颜色分量:绿色, 范围0-255             |
| colorBlue      | 颜色分量:蓝色, 范围0-255             |
| duration       | 这个时间片的持续时间，单位为毫秒(ms) |
| oldFilm        | 老电影效果，0代表关闭，1代表开启     |
| dotFilm        | 点状电影效果，0代表关闭，1代表开启   |
| reflectionFilm | 反射电影效果，0代表关闭，1代表开启   |
| glitchFilm     | 故障电影效果，0代表关闭，1代表开启   |
| rgbFilm        | RGB电影效果，0代表关闭，1代表开启    |
| godrayFilm     | 光辉效果，0代表关闭，1代表开启       |



除此之外在每个关键帧的尾部还有关键字duration，用于控制这一帧到下一帧的持续时间，例如一个简单的亮度变化动画：

```javascript
[
  {
    "brightness": 1.0,  // 始状态：亮度为1.0（取值范围为0-1，1为正常亮度）
    "duration": 0       // 起始帧持续时间（0表示设置好初始状态后立即进入下一帧）
  },
  {
    "brightness": 0.4,  // 末状态：亮度降低到0.4（变暗）
    "duration": 600     // 该阶段持续600毫秒
  }
]
```

![点击并拖拽以移动](data:image/gif;base64,R0lGODlhAQABAPABAP///wAAACH5BAEKAAAALAAAAAABAAEAAAICRAEAOw==)

需要注意的是，末状态不会随着动画的结束而自动返回立绘或图片的初始状态（也就是动画结束后会保留），想要“变回去”需要另外再写一个动画。

其中，position和rotation拥有子控件x和y，分别对应x轴效果和y轴效果，使用语法如下：

```javascript
[
  {
    "scale": {
      "x": 1,        //x轴旋转为1倍
      "y": 1
    },
    "position": {
      "x": -50，     //x轴偏移为-50，单位为px
      "y": 0
    },
    "duration": 0
  },
  {
    "scale": {
      "x": 1,
      "y": 1
    },
    "position": {
      "x": 0,        //变化后的末状态的x偏移为0，这个动画的实际效果相当于
      "y": 0         //图像从-50px的位置经过500毫秒线性移动到了0px位置
    },
    "duration": 500
  }
]
```

![点击并拖拽以移动](data:image/gif;base64,R0lGODlhAQABAPABAP///wAAACH5BAEKAAAALAAAAAABAAEAAAICRAEAOw==)

怎么样，还是挺好理解的吧。

## 3.自定义动画的原理拆解

webgal所使用的动画是json文件，json本质上是纯数据形式的js对象。（希望你有一点点web开发或是前端的基础，不过没有也不要紧，可以直接看第六节交给ai写。）

自定义动画的结构如下：

```javascript
[
    {
        "xxx":xxx
    },
    {
        "xxx":xxx
    }
]

//其中，[]是一个对象
//{}是一个数组，数组内的xxx是存放的字符串或数字以及对应的值
//js语法要求一个对象内存在多个数组时要用","隔开（最后一个不需要写）

//无论如何，动画请按照这个结构编写，duration请设置在数组的尾部。例如：

[
    {
        "xxx":xxx,    //记得用逗号隔开
        duration:0
    },
    {
        "xxx":xxx
    }
]

//在js中，数组的一个元素也可以是数组，所以偏移和旋转会有上面的写法。
//不要把duration等属于最外层数组的元素写进属于偏移或者旋转的数组，否则不会生效。
```

![点击并拖拽以移动](data:image/gif;base64,R0lGODlhAQABAPABAP///wAAACH5BAEKAAAALAAAAAABAAEAAAICRAEAOw==)

## 4.案例：一个简单的nohover动画编写

说了这么多，我们来试试实战，写一个简单的动画。

假设小琴有一个聚焦动画，需求如下：

（孩子们别笑话我，主播随便画的）

两个人同时在场时，讲话的一方亮度正常，而不讲话的一方亮度变暗，看起来就像聚光灯打在讲话一方上，大致图片如下：

![img](https://i-blog.csdnimg.cn/direct/19752d60769e4dca9438e0c970f928d9.jpeg)![点击并拖拽以移动](data:image/gif;base64,R0lGODlhAQABAPABAP///wAAACH5BAEKAAAALAAAAAABAAEAAAICRAEAOw==)编辑

不难分析出，始状态应该是立绘的原始状态，然后经过一小段时间（先假设是100毫秒吧！）后变为末状态，末状态的亮度和饱和度都略微变低，那么不难写出：

```javascript
[
  {
    "brightness":1,
    "saturation":1,
    "duration": 0
  },
  {
    "brightness":0.7,
    "saturation":0.8,
    "duration": 100
  }
]
```

![点击并拖拽以移动](data:image/gif;base64,R0lGODlhAQABAPABAP///wAAACH5BAEKAAAALAAAAAABAAEAAAICRAEAOw==)

还是很好实现的吧！

当我们想退出nohover动画的末状态时，可以新写一个动画nohover-out，只需要对调一下始末状态就好了！非常简单。

## 5.动画的导入以及使用

有时候你下载了别人的动画，或者自己写好了新的动画，下一步就是导入使用了。

根据webgal官方文档的内容

> 你需要在 `animationTable`中加上你的自定义动画的文件名（不需要后缀名）
>
> 在文件 `animationTable.json......`

希望你的动画没有写错位置，通常情况它应该在release\public\games\yourgame\game\animation中

打开这个路径，你会看到如下文件夹：

![img](https://i-blog.csdnimg.cn/direct/21f83a7103b74983904b9a1d75e1b573.png)![点击并拖拽以移动](data:image/gif;base64,R0lGODlhAQABAPABAP///wAAACH5BAEKAAAALAAAAAABAAEAAAICRAEAOw==)编辑

最顶部的animationTable.json就是我们的目标文件了，这个json不是动画，而是储存“有哪些动画”的。打开后结构如下：

![img](https://i-blog.csdnimg.cn/direct/cda5f6833698490d8154f836f3c9365b.png)![点击并拖拽以移动](data:image/gif;base64,R0lGODlhAQABAPABAP///wAAACH5BAEKAAAALAAAAAABAAEAAAICRAEAOw==)编辑

这里就是文件夹内的所有动画，如果你新写了动画，就在最后打个逗号接着写下新的动画的名字。然后保存关闭。（不需要写后缀！例如for-cg不需要写成for-cg.json）

回到浏览器页面，请刷新浏览器，然后就能在可视化区域中找到你新的动画了。

（由于预设的动画会用到的不多，因此你可以套一个文件夹，把预设动画扔进去，然后外层只留你自己写的动画）

## 6.善用ai编写简单的动画

叽里呱啦说什么呢，孩子们我是小刻啥也不会，这些还是太有操作了，我完全不会怎么办。

没关系的，没关系的，这时候只要掏出ai一切都会好起来的。

由于铸币lz注册gemini一直失败，这里一怒之下使用我们超级无敌好用的国产ai豆包（是的孩子们豆包的本地化确实好用）

只需要把动画文档的链接：[孩子们，复制我就对了](https://docs.openwebgal.com/webgal-script/animation.html#创建动画) 丢给豆包，然后输入对动画的描述（请尽可能详细一点，精确到每个关键帧的变化），然后等几秒钟就写好了：

![img](https://i-blog.csdnimg.cn/direct/7adfbf1b459149dd9feb44a77faf4d57.png)![点击并拖拽以移动](data:image/gif;base64,R0lGODlhAQABAPABAP///wAAACH5BAEKAAAALAAAAAABAAEAAAICRAEAOw==)编辑

**孩子们，豆包真的是太超模了，我毕业以后能肘的过ai吗？man8 out！**

好啦就这么多了，我们下次再见！