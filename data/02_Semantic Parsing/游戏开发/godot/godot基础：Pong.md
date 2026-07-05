---
title: godot基础：Pong
published: 2026-04-08T09:54:01
tags: [博客文章, godot]
category: '开发日志'
---

来试试一些实战性的东西吧！

# Pong！

Pong是世界上最古老的电子游戏之一。

```json
##############################################
#                                            #
#                 1      0                   # 
#                                            #
#                    |                       #
#                    |                       #
#             I      |               O       # 
#                    |                       #
#                    |                       #
#                    |                       #
#                                            #
##############################################
```

Pong本质上是电子乒乓球，接住球->正常反弹，否则对方计分一分。

今天我们要在godot中实现这个游戏的玩法。



# 认识节点

在此之前，我们已经认识过了`node2d`这个节点，今天来认识`area2d`。

相比node2d，area2d可以做空间检测，位置碰撞等。相比之下，如果只想摆放位置，只放`node2d`即可。

但是不能只摆放位置，还需要`collisionshape2d`这个节点（本文简称collision）是为节点设置碰撞箱大小的，有了碰撞箱检测，就能实现一些简单的交互效果。

> 你可以在检查器中找到Shape，为一个物体添加任意的碰撞箱，在这个游戏中，可以添加圆形碰撞箱。



添加完碰撞箱，还需要贴图，虽然你可以直接给`area2d`设置颜色，但这里还是使用`sprite2d`为其设置多种多样的贴图。

添加完毕贴图，记得调整一下贴图大小，让它和碰撞箱差不多大。



> 值类型：Vector2
>
> ​	这是一个2d坐标的类型，封装了很多常用的方法，如`distance_to(other)`等。想要处理2d坐标的变化，就需要使用到Vector2.



`colorrect`节点，显示一块纯色矩形，是最简单的背景板。



# 小球的代码编写示范

点击小球根节点创建脚本，进入后可以看到如下内容：

```gdscript
extends Area2D

func _ready():
    pass

func _process(delta):
    pass
```



这里的pass是暂空留着的，当然我们需要改动一下：



```gdscript
extends Area2D

func _ready():
    pass

func _process(delta):
    position = position + Vector2(1, 0)
    #这里Vector2表示一个坐标轴，每次在position的基础上，横坐标+1，纵坐标不变。
    #特殊：_process函数有个值delta，为每帧执行，会导致不同性能的电脑上运行速度不一样。
```



修改完毕后，启动游戏可以发现小球开始向右移动了！



> 类型标注：
>
> ​	gdscript像JavaScript一样，用var定义的变量可以切换储存信息。但有时候，我们只希望某一个变量只储存一个类型的变量，就可以使用类型标注：
>
> ​	var vec:Vector2=Vector(5,0)



在上面创建好vec后，我们就可以直接在函数中使用了：

```gdscript
position = position + vec
```



# 自定义函数

接下来我们需要自定义函数，让小球出界时候回到初始位置。

```gdscript
var = init_position

func _ready():
	init_postition = position
	pass
	
func _process(delta):
	#前略
	if position.x > 500 :
		self.rest()
		#也可以省略self，不过写上去更清晰。

func rest():
	position = init_position
```



# 常识积累

```json
1152，648
这是godot默认的窗口大小，设置这个值，就可以让背景板恰好铺满窗口，是非常常用的测试参数。
```

