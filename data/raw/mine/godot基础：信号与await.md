---
title: godot基础：信号与await
published: 2026-04-08T09:54:01
tags: [博客文章, godot]
category: '开发日志'
---

《事件和委托》

听起来是不是很像？其实程序的这些东西，很多事都是很接近的。信号只管发送和接受，而不关心谁发出，谁接受，因此在解耦上非常良好。godot的设计哲学正是节点+信号的模式。

# 信号

- 信号机制是Godot内置的一种调用函数的机制。
- 它需要一个对象的信号与另一个对象的函数绑定。信号发射后，程序会执行函数的调用。如果双方的对象，方法不存在，只会警告开发者而不会发生奔溃退出。



# 信号的使用演示

所以说，嘿，我能在哪里看到信号呢？

试试这里：

![godot信号](https://i.postimg.cc/rpkbwSwq/QQ20260408-212843.png)

你可以自行检查这些信号的说明信息。

这些信号是godot内置的信号，在一定条件下由godot自动触发。



# 自定义信号

自定义信号需要使用一个`signal` 关键字，它意味着接下来的这段是一个信号。

假设玩家受伤，屏幕会播放受伤的动画，那么信号是这样写的：

```GDScript
signal player_hurt (type: str)

func _ready():
	# 此处手动绑定信号，监听自己发出的信号。
	connect("player_hurt", _on_player_hurt)
	# 发射信号，传递参数，伤害类型为法术
	emit_signal("player_hurt","SPD")

func _on_player_hurt(type:str)
	print("受到伤害类型为：",type)
```

这种方式是代码绑定，当你创建了信号，也可以在右侧的图形化区域的节点中进行绑定。
