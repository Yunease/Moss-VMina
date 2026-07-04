---
title: 初识renpy
published: 2026-02-10T14:12:01
tags: [博客文章]
category: '开发日志'
---

大家好，这里是小琴。

我参与开发的国产AVG文游 “你是如此特别” （暂称） 在今天正式立项准备参与开发，我也将在这个系列中更新自己的开发日志。



# 一切起始之时



我们尝试一个简单的小游戏：



```renpy
label start:

    "vilstia" "烧灼，蔓延。"
    
    "yunease" "杀戮，钻孔"
```



label语句用于给程序中的某个脚本节点命名，在这里是start标签，start标签是特殊标签，也不能删除，程序在开始会直接进入start。这一点有点像webgal的start.txt，反正都是一样的对吧。



特别一提的是，因为rpy是类python语言，所以对缩进有着严格的要求：



```renpy
label scene1:
    //需要四个空格
    "vilstia" "火焰。"
```



这里的句子缩进后的字符串就是say语句，say语句的旁白这样写：



```renpy
label scene2:
    "vilstia" "要我去做什么。"
    //这个就是旁白，没有speaker
    "她要做什么呢？"
    "vilstia" "是，我说过，\"可你情愿看那些灰烬\"?"
```



就像c语言一样，renpy也有转义字符，因为直接使用 `" "` 会出现解释错误，因此需要使用反斜杠 `\` 来实现转义。



# 来到新世界

## 宏定义



如果反复输入角色名，有一点太麻烦了，可以使用宏定义：



```renpy
define v = character('vilstia',color="#ffffff")
define m = character('me',color="#ffffff")

label scene3:
	v "憎恨是水。"
	m "但愿如此。"
```



这里的 `color` 有些类似html或是css里的属性，可以使用十六进制表示。



## 图像（image）



我们也需要一些立绘或是背景，请参考如下代码：



```renpy
label scene4:

    scene bg meadow

    "风啊，您就这样吹拂吧。"

    "谁也无法拦住您，可是......"

    "您要去到哪里去呢？"

    show sylvie green smile
```



在这里的 `scene` 语句会清除所有图像（这一点和webgal不一样，webgal需要手动清除所有图像），而 `show` 语句会在背景上显示一个精灵，并且根据预设改变展示。



在renpy中，每个图像都有一个 `tag` 和 可选属性 `attribute` 。这些属性必须满足一般变量的命名规范。

在上面这个场景中， `sence` 的 tag 是 bg，属性是 meadow。通常来说，背景图像应该使用 bg 作为 tag 标签。

而 `show` 语句中的 tag 是 sylvie ，属性是 green 和 smile 。

tag 类似 webgal 的 id ，一次只能展示一张带有相同 tag 的图像，当出现新的图像，会直接替换掉原本的图像。



>Ren’Py会在images目录下搜索图像文件，可以通过启动器(launcher)的“打开目录”选项里选择“images”完成配置。Ren’Py能使用PNG或者WEBP文件作为角色美术资源，JPG、JPEG、PNG或者WEBP文件作为背景美术资源。文件的命名相当重要，Ren’py将使用除去扩展名后，强制字母变为小写的文件名来作为图象名。



例如，images目录下的这些文件，定义了下列图像：

- “bg meadow.jpg” -> `bg meadow`
- “sylvie green smile.png” -> `sylvie green smile`



> **注意** 因为文件名会被转换为小写字母。



图像可以被放在images目录的子目录(子文件夹)中。目录名忽略，只使用文件名定义图像名。这一点比webgal方便很多。



`heid` 语句：用来隐藏图像。

例如：

```renpy
label leaving:
	v "如你所愿"
	hide sylvie
	m "人呢！！"
```



注意， `sence` 语句会直接清除场景，所以不用特别写 `hide` 。



`image` 语句的写法类似宏定义，但是image不会使用renpy默认的参数，需要玩家自己定义。



```renpy
image logo = "renpy logo.png"
image happy = "happy.png"
```



## 转场



在两个场景之间，直接切换的效果非常生硬。转场发生最后一个交互（点击对话等）等到下一个scene show或hide之间。



```renpy
label scene5:
	scene bg meadow
	with fade
	v "楼阁上的浮灰......"
	"她没有玩笑的意味"
	show sylvie green smile
	with dissolve
	v "我会回应你的期许，憎恨也会如约而至。"
```



这里的 `with` 语句决定了转场使用的效果，最常用的是 `dissolve` 和 `fade` 。

如果存在多个scene、show、hide，那么在其之后的转场对其上所有语句都生效了。



```renpy
    scene bg meadow
    show sylvie green smile
    with dissolve
```



“bg meadow”和“sylvie green smile”图像会同时使用dissolve转场。如果想要每次只让其中之一使用dissolve转场，你需要写两个转场语句：



```renpy
    scene bg meadow
    with dissolve
    show sylvie green smile
    with dissolve
```



场景meadow里有第一个dissolve效果，而角色sylvie里有第二个dissolve效果。如果你想要立刻展现meadow场景，然后使用转场效果展现角色sylvie，你可以这样写：



```renpy
    scene bg meadow
    with None
    show sylvie smile
    with dissolve
```



这里的“None”被用于标识一个特殊转场效果，对玩家来说主界面没有产生任何特殊效果。



## 位置（position）



图像在展示时默认水平居中，图像底部与界面底部相接。这样设计通常对背景和单个角色没问题，但当界面上需要展现1个以上角色时，重新调整图像位置也是十分合理的。同样，基于剧情需要，调整单一角色的图像位置也可以理解。



```renpy
     show sylvie green smile at right
```



为了重新调整图像位置，需要在show语句中添加一个at分句。at分句指定了图像的展示位置。Ren’Py中包含了多个域定义的位置关键字: `left` 表示界面左端， `right` 表示屏幕右端， `center` 表示水平居中(默认位置)， `truecenter` 表示水平和垂直同时居中。



当然你可以自定义位置关键字。



## 音乐和音效



大多数Ren’Py游戏都会播放背景音乐。音乐播放需要使用play music语句。play music语句将语句中指定的文件名识别为一个音频文件并播放。Ren’Py跟识别音频文件名并在game目录下寻找关联文件。音频文件应该是opus、ogg vorbis或者mp3格式的文件。



```renpy
    play music "audio/illurock.ogg"
```



更换音乐时，我们可以使用一个fadeout and fadein分句，fadeout and fadein分句用于旧音乐的淡出和新音乐的淡入。



```RENPY
    play music "audio/illurock.ogg" fadeout 1.0 fadein 1.0
```



queue music语句表示，在当前音乐播放完毕后播放的音频文件。



```renpy
    queue music "audio/next_track.opus"
```



乐播放可以使用stop music语句停止，这个语句也可选用fadeout分句。



```renpy
    stop music
```



音效可以使用play sound语句来播放。与音乐不同，音效不会循环播放。



```renpy
    play sound "audio/effect.ogg"
```



在 `game/audio` 目录中的音频文件，如果其文件名去掉文件扩展名后符合Python变量的命名规则(以字母开头且仅包含英文字母、数字或下划线)， 则可以直接不带引号，直接使用文件名播放音频文件。

例如，存在一个音频文件 `game/audio/illurock.ogg` 。我们可以直接在脚本中写：



```renpy
    play music illurock
```



## pause语句



pause语句可以让整个Ren’Py进程暂停，直到出现鼠标单击事件。



```renpy
	pause
```



如果pause语句中给定一个数字，就只会暂停数字对应的秒数。



```renpy
    pause 3.0
```



## 结束游戏



使用 `return` 语句来结束游戏，不需要做任何事。



```renpy
    ".:. Good 结局。"

    return
```



至此，已经足够做一个没有任何分支选项的视觉小说了。



# 触摸一下另一个世界的碎片吧！

## menu，label和jump语句



menu语句能够给玩家提供一个分支选项:

```renpy
	v "温和的星体，它们要做什么呢"
menu:
	"在发光。":
		jump light
	"在死亡。":
		jump die
label light:
	m "在发光，星星因为发光才会被我们看到。
	jump next
label die:
	m "在死亡，然后坍缩下去。"
	jump next
label next:
	v "好......真奇怪。"
```



> 注意一下缩进。



如果label后面相关的语句块(block)之后没有jump语句，Ren’Py会顺序执行后面的语句。最后的jump语句在技术上不是必须的，不过带上一个会让游戏流程显得更清晰。



## 使用default、Python和if语句实现flag(标识)



上面那些语句已经足以用于制作某些游戏，其他一些游戏则需要保存数据及提取数据。例如，制作者需要游戏记下玩家做出的一个选择，先返回主线流程中，并在后面的流程中根据之前的选择出现对应的游戏变动，这是个合理的需求。这就是Ren’Py支持内嵌Python代码的原因。

这一段，我们将演示如何存储一个flag(标识)，该flag(标识)包含了玩家做过的某个选择。我们需要先初始化flag(标识)，在start脚本标签(label)之前，使用default语句。



```renpy
default fa_Name = 0

label start:

    v "怎么样，你喜欢我吗？"
menu:
	"我喜欢！":
		jump like
	"一般般...":
		jump dislike
label like:
	$ fa_Name += 1
label dislike:
	$ fa_Name -= 1
```



以美元标志符“$”开头那行文本会被识别为Python语句。assignment(赋值)语句将这里的“book”判定为一个变量而不是一个值。Ren’Py已经支持一些其他包含Python代码的办法，例如多行的Python语句。



需要检查flag(标识)时，请使用if语句：



```renpy
if fa_Name >= 3:
	jump goodEnding
else:
	jump badEnding
```



Python变量不仅仅可以是简单的布尔值。变量也可以存储玩家名字、分数或者其他一些想要记录的事情。由于Ren’Py支持Python编程语言的所有功能，许多想法都可能实现。



## 模板文件夹：



创建的项目中game目录下会包含下列目录和文件。

- **audio/**

  该目录用户保存音频文件。详见 [音频](https://doc.renpy.cn/zh-CN/audio.html)。

- **cache/**

  该目录包含缓存文件。创作者不需要编辑这些文件。

- **gui/**

  该目录保存GUI使用的图片文件。详见 [GUI定制化指导](https://doc.renpy.cn/zh-CN/gui.html#gui)。

- **images/**

  该目录用于保存图片文件。详见 [显示图像](https://doc.renpy.cn/zh-CN/displaying_images.html)。

- **tl/**

  该目录保存翻译文件。详见 [多语言支持](https://doc.renpy.cn/zh-CN/translation.html)。

- **gui.rpy**

  所有GUI相关变量都定义在该文件中。详见 [GUI定制化指导](https://doc.renpy.cn/zh-CN/gui.html#gui)。

- **options.rpy**

  配置和构筑相关变量，一部分环境设定配置，以及一部分GUI的变量都定义在该文件中。 详见 [配置项变量](https://doc.renpy.cn/zh-CN/config.html)、[环境设定配置](https://doc.renpy.cn/zh-CN/preferences.html)、[构建发行版](https://doc.renpy.cn/zh-CN/build.html) 和 [GUI定制化指导](https://doc.renpy.cn/zh-CN/gui.html#gui)。

- **screens.rpy**

  界面都定义在该文件中。创作者可以编辑该文件，实现 [高级GUI定制化](https://doc.renpy.cn/zh-CN/gui.html#more-advanced-gui)。 详见 [样式(style)](https://doc.renpy.cn/zh-CN/style.html)、[样式特性(property)](https://doc.renpy.cn/zh-CN/style_properties.html)、[界面和界面语言](https://doc.renpy.cn/zh-CN/screens.html)、[界面行为(action)、值(value)和函数](https://doc.renpy.cn/zh-CN/screen_actions.html)、[特殊界面名称](https://doc.renpy.cn/zh-CN/screen_special.html) 和 [界面语言优化](https://doc.renpy.cn/zh-CN/screen_optimization.html)。

- **script.rpy**

  该文件用于在剧情脚本，并可以引入其他脚本文件。 创作者也可以根据需要添加或删减 `.rpy` 文件。 详见 [编程语言基础](https://doc.renpy.cn/zh-CN/language_basics.html)。

- ***.rpyc**

  这些文件是 `.rpy` 文件编译后的产物，用于节省加载时间。 如果不删除对应的 `.rpy` 文件，仅修改这些文件是没有效果的。详见 [编程语言基础](https://doc.renpy.cn/zh-CN/language_basics.html)。