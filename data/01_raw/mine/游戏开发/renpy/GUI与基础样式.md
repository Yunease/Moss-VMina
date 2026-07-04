---
title: GUI与基础样式
published: 2026-02-10T14:12:01
tags: [博客文章]
category: '开发日志'
---

大家好，这里是小琴，朋友，愿真主赐我们成功。

接下来我们一起学习renpy的GUI部分，自定义也是很重要的。



# GUI图形用户接口



默认创作者正在使用新样式的Ren’Py GUI(定制化配置包含在 `gui.rpy` 文件中)。使用老版本的GUI(使用 `screens.rpy` 文件进行定制化配置)的创作者，应该把本页内容当作是深度定制化指导。



## 简单GUI定制化



GUI定制化工作包含几个简单部分，对所有项目都适用而不仅仅针对最简单的视觉小说。这些定制化工作的共同点是，都不需要编辑 `gui.rpy` 文件。这些定制化会给GUI带来一些微妙的变化，而不是让GUI彻底改头换面。



## 更改颜色和尺寸

### 

这是最简单的事情。



## options.py



`options.rpy` 文件中会有一堆配置项会被GUI使用，可以设置 true 或是 false 启动或是隐藏。



- [`config.name`](https://doc.renpy.cn/zh-CN/config.html#var-config.name)

  一个字符串，表示该游戏的标题名称。这个字符串同时用在窗口标题和GUI需要显示游戏标题的地方。

- `gui.show_name`

  这个配置项应该被设置为False，用于在画面主菜单中隐藏标题名字和版本号。(因为，标题应是被“镶嵌”在主菜单的图片中)

- [`config.version`](https://doc.renpy.cn/zh-CN/config.html#var-config.version)

  一个字符串，表示游戏版本号。默认GUI中，很多地方都会向用户显示。 此外，也可以用于显示错误信息或问题追踪。

- `gui.about`

  在关于(about)界面上的附加文本内容。如果你想要展示多行的credits(制作人员信息)，可以使用 \n\n 换行。



这是一个包含以上配置项的样例:

```renpy
define config.name = _('Old School High School')

define gui.show_name = True

define config.version = "1.0"

define gui.about = _("Created by PyTom.\n\nHigh school backgrounds by Mugenjohncel.")
```



为了省事，gui.about的定义使用3个双引号，中间可以包含换行。

```renpy
define gui.about = _("""\
Created by PyTom.

High school backgrounds by Mugenjohncel.""")
```



## 游戏和主菜单背景图像

GUI使用的图像文件在game/gui目录下，也可以通过启动器的“打开目录：gui”选项打开对应的目录。比较重要的几个图片文件为：

- gui/main_menu.png

  用于主菜单的所有界面背景的图片文件。

- gui/game_menu.png

  用于游戏菜单所有界面背景的图片文件。



## 窗口图标



可以通过更换 `gui/window_icon.png` 改变窗口图标。



注意，改变gui/window_icon.png后，只对游戏正在运行时的图标有效。想要改变Windows平台的“.exe”文件和mac平台的应用程序图标，我们需要看看 [生成文档](https://doc.renpy.cn/zh-CN/build.html#special-files).



## 中级GUI定制化



中级GUI会改变一些配色，字体和图片，其实说起来和webgal的差不多啦



绝大多数修改都可以通过修改 `gui.rpy` 来实现。

这个板块很简单，是个人看一眼也会了，就不多说了。



## 对话

- gui/textbox.png

  该文件包含了文本窗口的背景，为say(说话)界面中的一部分。虽然图片大小应该跟游戏分辨率吻合，但是文本内容应该只在中心左右60%的宽度范围内显示，两边各预留20%的边界。



- define gui.text_font = "ArchitectsDaughter.ttf"[link](https://doc.renpy.cn/zh-CN/gui.html#var-gui.text_font)

  该项设置对话文本、菜单、输入和其他游戏内文字的字体。字体文件需要存在于game目录中。**(译者注：“ArchitectsDaughter”字体不支持中文。后续截图中使用的是类似效果的“方正咆哮体”。)**



## 选项菜单



**gui/button/choice_idle_background.png**

**gui/button/choice_hover_background.png**

第一个就是正常情况显示的图像，第二个是hover状态下的。



### Borders(边界)

有一些GUI组件，例如按钮(button)和条(bar)，使用可伸缩的背景的话，还可以配置Borders(边界)对象。在讨论如何定制化按钮和条(bar)之前，我们首先描述一下边界的实现机制。

Borders(边界)是可视组件中 [`Frame()`](https://doc.renpy.cn/zh-CN/displayables.html#Frame) 类的可选成员。 一个Frame对象会使用一个图片，然后分割为9块——4块角落，4个边条及1块中心区域。4个角落总是保持相同的尺寸，左右边条水平对齐，上下边条垂直对齐，中心区域在两个维度上都对齐。

Borders(边界)对象按照“左、上、右、下”的顺序，依次给定了边界的尺寸。（注意web是上顺时针）



一个Border对象也可以被给定padding(内边距)，包括负值的内边距会让child能超出原有范围叠加在边界上。例如，这样的Borderss:

```renpy
Borders(40, 40, 40, 40, -20, -20, -20, -20)
```



## 按钮

- button

  基础按钮。在用户接口中，对用户行为进行引导。

- choice_button

  用于游戏内菜单的单项选择按钮。

- quick_button

  游戏内快速进入游戏菜单的按钮。

- navigation_button

  在主菜单和游戏菜单中，用于引导至其他界面和开始游戏的按钮。

- page_button

  读档和存档界面用于翻页的按钮。

- slot_button

  存档槽位按钮，包含了一个缩略图、存档时间和一个可选的存档名字。后面我们会谈到这些内容的具体细节。

- radio_button

  在界面中多组单项选择的按钮。

- check_button

  提供勾选项的按钮。

- test_button

  环境设定设置界面上，用于音频回放的按钮。这个按钮应该在垂直高度上与滑块一致。

- help_button

  用于玩家选择需要何种帮助的按钮。

- confirm_button

  用在选择“是”或者“否”的确认界面的按钮。

- nvl_button

  用于NVL模式下菜单选项的按钮。

下面这些图片文件用于定制化按钮背景，前提是这些文件存在。

- gui/button/idle_background.png

  用于未获取焦点按钮的背景图片。

- gui/button/hover_background.png

  用于获取焦点按钮的背景图片。

- gui/button/selected_idle_background.png

  用于被选择但未获取焦点按钮的背景图片。这个图片属于可选的，仅在 `idle_background.png` 图片存在的情况下才有用。

- gui/button/selected_hover_background.png

  用于被选择并获取到焦点按钮的背景图片。这个图片属于可选的，仅在 `hover_background.png` 图片存在的情况下才有用。

更多特定的背景可以用于对应类型的按钮，是否适用可以通过图片名的前缀判断。例如， `gui/button/check_idle_background.png` 可以用作check button中没有获取焦点选项的背景。

在radio button和check button中，有4个图片文件可以用作前景修饰，用于标识该选项是否被选中。

- gui/button/check_foreground.png, gui/button/radio_foreground.png

  这两个图片用于check button或radio button未被选择的选项。

- gui/button/check_selected_foreground.png, gui/button/radio_selected_foreground.png

  这两个图片用于check button或radio button被选中的选项。

下面的几个配置项设置了按钮的各类属性:

- define gui.button_width = None[link](https://doc.renpy.cn/zh-CN/gui.html#var-gui.button_width)

  

- define gui.button_height = 64[link](https://doc.renpy.cn/zh-CN/gui.html#var-gui.button_height)

  按钮的宽度和高度，使用像素作为单位。如果值配置为“None”，系统会基于两项内容自定义一个合适的大小。这两项内容之一是按钮上的文本尺寸，另一项则是下面提到的borders(边界)。



## 滑块

滑块(slider)是一类用在环境设定界面的条(bar)，允许玩家可以根据自身喜好调整大量的数值。GUI默认只使用横向的滑块，不过游戏中也往往会用到垂直的滑块。

滑块(slider)可以使用以下图片进行定制化：

- gui/slider/horizontal_idle_bar.png, gui/slider/horizontal_hover_bar.png, gui/slider/vertical_idle_bar.png, gui/slider/vertical_hover_bar.png

  用于空闲和指针悬停状态下垂直或水平滑块的背景图片。

- gui/slider/horizontal_idle_thumb.png, gui/slider/horizontal_hover_thumb.png, gui/slider/vertical_idle_thumb.png, gui/slider/vertical_hover_thumb.png

  用于条(bar)的thumb(可拖动部分)的图片。

以下配置项也会被用到:

- define gui.slider_size = 64[link](https://doc.renpy.cn/zh-CN/gui.html#var-gui.slider_size)

  水平滑动块的高度，或者垂直滑块的宽度。









