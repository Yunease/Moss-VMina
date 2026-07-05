---
title: Godot2d拖拽窗口时窗口异常闪现及无法正确释放问题的结局办法
tags: [博客文章, godot]
description: '没有gdscript，这里用语法相近的c#，简单看个语法高亮）运行游戏后，发现按下后窗口会闪现到屏幕右下角，而且松开鼠标后无法释放。'
published: 2025-11-06T15:48:01
---

 最近我放弃了unity，开始研究godot2d，写了如下代码（已经删减了注释）：

```cs
extends Node2D

var click_mouse_position := Vector2i.ZERO
var click_window_position := Vector2i.ZERO
var is_dragging: bool = false

func _process(_delta: float) -> void:
	if is_dragging:
		var mouse_pos = DisplayServer.mouse_get_position()
		var delta = mouse_pos - click_mouse_position
		get_window().position = click_window_position + delta

func _on_area_2d_input_event(viewport: Node, event: InputEvent, shape_idx: int) -> void:
	if event is InputEventMouseButton:
		if event.button_index == MOUSE_BUTTON_LEFT:
			if event.pressed:
				click_mouse_position = event.global_position
				click_window_position = get_window().position
				is_dragging = true
			else:
				is_dragging = false
```

![点击并拖拽以移动](data:image/gif;base64,R0lGODlhAQABAPABAP///wAAACH5BAEKAAAALAAAAAABAAEAAAICRAEAOw==)

没有gdscript，这里用语法相近的c#，简单看个语法高亮）

运行游戏后，发现按下后窗口会闪现到屏幕右下角，而且松开鼠标后无法释放。



笔者的这篇文章除了想说解决问题的办法，更想说是怎么找到问题的。

先分析逻辑是哪里错了。能够控制窗口移动的方法是get_window()中，定位后发现移动逻辑是鼠标初始位置+变化位置。

变化位置的计算方法就在_process中，经过排查发现此处逻辑正确，因此问题应该出在click_mouse_position这个变量的设置中，查找一番后发现在_on_area_2d_input_event中，设置click_mouse_position的语句是这个：

```cs
click_mouse_position = event.global_position  # 错误的位置来源
```

![点击并拖拽以移动](data:image/gif;base64,R0lGODlhAQABAPABAP///wAAACH5BAEKAAAALAAAAAABAAEAAAICRAEAOw==)

这里用的是全局窗口，和玩家控制的鼠标无关，会直接先定位到屏幕右下角去，然后_process函数才会生效。

正确的代码是：

```cs
click_mouse_global = DisplayServer.mouse_get_position()  # 正确的位置来源
```

![点击并拖拽以移动](data:image/gif;base64,R0lGODlhAQABAPABAP///wAAACH5BAEKAAAALAAAAAABAAEAAAICRAEAOw==)

解决完这个问题后，还要解决松开鼠标不释放的问题：

和刚才的思路一样，先反思自己控制松开窗口的代码写在哪个函数里了，显然是_on_area_2d_input_event里，仔细研究后发现逻辑有误：

```cs
func _on_area_2d_input_event(viewport: Node, event: InputEvent, shape_idx: int) -> void:
	if event is InputEventMouseButton:
		if event.button_index == MOUSE_BUTTON_LEFT:
			if event.pressed:
				click_mouse_position = event.global_position
				click_window_position = get_window().position
				is_dragging = true
			else:
				is_dragging = false
```

![点击并拖拽以移动](data:image/gif;base64,R0lGODlhAQABAPABAP///wAAACH5BAEKAAAALAAAAAABAAEAAAICRAEAOw==)

这里的逻辑嵌套明显有误，首先判断事件类型是鼠标后，先判断了是鼠标左键按下，如果是才会判断是否不是按下，这样只有按下不是左键才会松开，因此发生了错误。

修改后的代码如下：



```
extends Node2D

# 记录鼠标点击时的全局位置（屏幕坐标系）
var click_mouse_global: Vector2i = Vector2i.ZERO
# 记录点击时窗口在屏幕上的位置
var click_window_pos: Vector2i = Vector2i.ZERO
# 拖拽状态
var is_dragging: bool = false

func _process(_delta: float) -> void:
	if is_dragging:
		# 获取当前鼠标在屏幕上的绝对位置（与窗口无关的全局坐标）
		var current_mouse_global = DisplayServer.mouse_get_position()
		# 计算鼠标移动的差值（相对于点击时的位置）
		var delta = current_mouse_global - click_mouse_global
		# 用窗口初始位置 + 移动差值更新窗口位置
		get_window().position = click_window_pos + delta

# Area2D的输入事件回调（确保已在编辑器中绑定此信号）
func _on_area_2d_input_event(viewport: Node, event: InputEvent, shape_idx: int) -> void:
	# 只处理鼠标按键事件
	if event is InputEventMouseButton:
		# 仅关注鼠标左键
		if event.button_index == MOUSE_BUTTON_LEFT:
			# 鼠标左键按下：开始拖拽
			if event.pressed:
				# 记录鼠标在屏幕上的绝对位置（关键：用DisplayServer获取，而非event.global_position）
				click_mouse_global = DisplayServer.mouse_get_position()
				# 记录当前窗口在屏幕上的位置
				click_window_pos = get_window().position
				is_dragging = true
			# 鼠标左键释放：结束拖拽
			else:
				is_dragging = false
```

