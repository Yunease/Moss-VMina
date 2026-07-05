---
title: vs code背景图片设置教程（新版） background插件2.0版本设置电脑小白向教程
tags: [博客文章, 计算机基础, css]
description: 'images是文件路径，允许http协议和file协议，本地文件的话就是file啦，当然不能直接复制文件路径，比较方便的办法就是利用浏览器打开图片，然后在浏览器中复制文件的地址，这样就能获取到file路径了：'
published: 2024-11-22T15:46:01
---

 **目录**

[1.旧版json文件报警问题](#1.旧版json文件报警)

[2.下载/更新background插件](#2.下载%2F更新background插件)

[3.配置非全屏背景的background的json文件](#3.配置非全屏背景的background的json文件)

[4.配置全屏背景的background的json文件](#4.配置全屏背景的background的json文件)

[5.总结](#5.总结)

------



# 1.旧版json文件报警问题



这几天vs code的国人插件background迎来了更新，十分好用，但是json设置和旧版不一样。

旧版settings.json的配置文件：

```
    // /** 编辑器背景 */
    //     "window.titleBarStyle": "custom", //首先把标题栏改为非原生的
    //     "background.enabled": true,
    //     "background.customImages": [
    //        //  这个是图片地址 注意这个是左斜杠
    //         "file:///C:/Users/26420/Desktop/pixiv/none/1.jpg"
    //     ],
    //     //这些都像css那样可以改样式的
    //     "background.style": {

    //         "content": "''",
    //         "pointer-events": "none",
    //         "position": "absolute",
    //         "z-index": "99999",
    //         "width": "100%",
    //         "height": "100%",
    //         "background-position": "cover",
    //         "background-repeat": "no-repeat",
    //         "background-size": "cover",  
    //         "opacity": 0.2  //这个是设置透明度
    //     },
```

![点击并拖拽以移动](data:image/gif;base64,R0lGODlhAQABAPABAP///wAAACH5BAEKAAAALAAAAAABAAEAAAICRAEAOw==)

如果你打开settings.json，就会发现这里有了警告，要求你使用新版的规范：

![img](https://i-blog.csdnimg.cn/direct/5a80cba341984c1cbfa356d49d604eef.png)![点击并拖拽以移动](data:image/gif;base64,R0lGODlhAQABAPABAP///wAAACH5BAEKAAAALAAAAAABAAEAAAICRAEAOw==)

这里全部选中注释掉就可以了，我们在后面写新版的配置。



# 2.下载/更新background插件



如果你以前下载过这个插件，在拓展里进行更新就可以了。如果你没有这个插件，则需要在拓展中搜索并下载background插件（不要下错了，下载和图片所示的图标一样的插件）

![img](https://i-blog.csdnimg.cn/direct/e3be69f0d7ee4e61831d2aa2600191cc.png)![点击并拖拽以移动](data:image/gif;base64,R0lGODlhAQABAPABAP///wAAACH5BAEKAAAALAAAAAABAAEAAAICRAEAOw==)

下载后，右下角会提示你需要重启vs code，点击重启就可以了。

常见问题：[vscode下载慢或失败等问题解决办法](https://blog.csdn.net/weixin_41263860/article/details/121305264)





# 3.配置非全屏背景的background的json文件



下载好background插件之后，点击左下角的小齿轮，打开设置：

![img](https://i-blog.csdnimg.cn/direct/7e5af7df6ce0428281145fd9f7121870.png)![点击并拖拽以移动](data:image/gif;base64,R0lGODlhAQABAPABAP///wAAACH5BAEKAAAALAAAAAABAAEAAAICRAEAOw==)

然后在弹出界面里搜索background：

![img](https://i-blog.csdnimg.cn/direct/be50896c7bad4a3a9704fa3fa64251e9.png)![点击并拖拽以移动](data:image/gif;base64,R0lGODlhAQABAPABAP///wAAACH5BAEKAAAALAAAAAABAAEAAAICRAEAOw==)

在拓展分类中找到background插件，在这里一共有五个选项，除去第一个默认开启并且可以勾选的之外，剩下的四个都需要在settings.json文件中进行配置。

这里简单介绍一下这四个东西分别是什么：



Editor——编辑区，也就是你编写代码的部分的背景，也就是这个：

![img](https://i-blog.csdnimg.cn/direct/e7ef6717850848d38d62c61f85037cfb.png)![点击并拖拽以移动](data:image/gif;base64,R0lGODlhAQABAPABAP///wAAACH5BAEKAAAALAAAAAABAAEAAAICRAEAOw==)

Fullscreen——全屏，如果应用这个就不能再写其他的设置了，不然会重叠（除非你对自己的重叠艺术很有自信），这个全屏包括了能够看到的全部界面。就像如下图，整个vs code都会以当前的图片作为背景生效：

![img](https://i-blog.csdnimg.cn/direct/ee16e2c2ac4748b2bc82a49fe51d6b68.png)![点击并拖拽以移动](data:image/gif;base64,R0lGODlhAQABAPABAP///wAAACH5BAEKAAAALAAAAAABAAEAAAICRAEAOw==)

Panel——面板区，也就是底边的调试输出等地方，如下：

![img](https://i-blog.csdnimg.cn/direct/b528e1d5cffb40059fedb434f39b88c0.png)![点击并拖拽以移动](data:image/gif;base64,R0lGODlhAQABAPABAP///wAAACH5BAEKAAAALAAAAAABAAEAAAICRAEAOw==)

Sidebar——侧边区，也就是唤出拓展的地方，如下：

![img](https://i-blog.csdnimg.cn/direct/ad2ac8bbbb604b059da094ccbd0b6842.png)![点击并拖拽以移动](data:image/gif;base64,R0lGODlhAQABAPABAP///wAAACH5BAEKAAAALAAAAAABAAEAAAICRAEAOw==)



回到刚才的设置区域，我们首先来配置editor，点击在settings.json中设置

![img](https://i-blog.csdnimg.cn/direct/5013b4e4bd414fd781f733a811442d85.png)![点击并拖拽以移动](data:image/gif;base64,R0lGODlhAQABAPABAP///wAAACH5BAEKAAAALAAAAAABAAEAAAICRAEAOw==)

打开设置文件可以看到预先帮你写了一部分代码，大概如下：

```json
{
  "background.editor": {
    "useFront": true,
    "style": {
      "background-position": "100% 100%",
      "background-size": "auto",
      "opacity": 1
    },
    "styles": [{}, {}, {}],
    "images": [],
    "interval": 0,
    "random": false
  }
}
```

![点击并拖拽以移动](data:image/gif;base64,R0lGODlhAQABAPABAP///wAAACH5BAEKAAAALAAAAAABAAEAAAICRAEAOw==)

style是css属性，不过学过css也不要紧的，先大概知道这个是设置样式的就可以了

background-position 设置的是图片的位置，一共有两个百分比的参数。如果想要让图片向右移动，则需要让第一个参数的数值变小（可以为负，超出部分会变成黑边），想要向左移动则需要改大。如果想要向下移动，则需要把第二个参数变大，想要向上移动则需要把第二个参数变小。这里可以使用css允许的数据单位，除了百分比，也可以使用px。

background-size是设置图片的尺寸，一般用auto就行了，如果你的图片像素太小会留出黑边的话，可以写cover充满整个区域。

opacity是透明度，推荐设置在0.1~0.3之间。

如果你对css有其他的了解，例如会写css滤镜，可以在styles中设置其他的css样式，这里就不展开讲了。

images是文件路径，允许http协议和file协议，本地文件的话就是file啦，当然不能直接复制文件路径，比较方便的办法就是利用浏览器打开图片，然后在浏览器中复制文件的地址，这样就能获取到file路径了：

![img](https://i-blog.csdnimg.cn/direct/3d53d19a021c4d02a72c1f94131140b5.png)![点击并拖拽以移动](data:image/gif;base64,R0lGODlhAQABAPABAP///wAAACH5BAEKAAAALAAAAAABAAEAAAICRAEAOw==)

例如这样↑

后面是要不要轮播，如果你设置了多个图片并开启轮播后，背景会时不时变化一下。



如果你能顺利配置Editor，那么相信其他的对你也没有难度：

![img](https://i-blog.csdnimg.cn/direct/eeff5c247d5040669081b91405a5b04b.png)![点击并拖拽以移动](data:image/gif;base64,R0lGODlhAQABAPABAP///wAAACH5BAEKAAAALAAAAAABAAEAAAICRAEAOw==)

![img](https://i-blog.csdnimg.cn/direct/44097636c57e445b9eb25fade89b1fa6.png)![点击并拖拽以移动](data:image/gif;base64,R0lGODlhAQABAPABAP///wAAACH5BAEKAAAALAAAAAABAAEAAAICRAEAOw==)

设置方式都是如出一辙的，在此不再赘述。



# 4.配置全屏背景的background的json文件

全屏和非全屏有一点点不太一样，如果你想要配置全屏，最好还是把非全屏的配置全部注释掉比较好，不然会出现重叠的问题。

这是我的全屏背景配置：

```
        "background.fullscreen": {
            "useFront": true,
            "style": {
                "background-position": "0% 100%",
                "background-size": "auto",
                "opacity": 0.8
            },
            "styles": [
                {},
                {},
                {}
            ],
            "images": ["file:///C:/Users/26420/Desktop/pixiv/none/3.jpg"],
            "interval": 0,
            "random": false
        },
```

![点击并拖拽以移动](data:image/gif;base64,R0lGODlhAQABAPABAP///wAAACH5BAEKAAAALAAAAAABAAEAAAICRAEAOw==)

大部分地方和非全屏一样，比较特殊的是透明度要调高一点。具体原理我并不清楚，可能是全屏的设置层叠方式不一样，不过大概是透明度越高越遮文字，因此推荐的透明度设置在0.8-0.9。



# 5.总结



也不知道要总结什么...萌新没怎么写过攻略，可能写的不太好，总之感谢看到这里的你，如果有什么问题可以在评论区发出来让大家看看帮帮忙。

如果对css技术有兴趣也可以自己学学，不过搞这个不如找点好看的图片，找图片可以去pixiv，也可以去堆糖，其他平台会有水印。