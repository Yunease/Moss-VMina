---
title: godot基础：resource
published: 2026-07-01T16:37:01
tags: [博客文章, godot]
category: '开发日志'
---

resource是没有位置，没有生命周期的资源文件，它不在场景树中，只负责储存数据。

所有的贴图，音频，脚本和材质，都是resource资源，可以被保存为.tres或者.res

```
extends Resource
class_name SkillData

@export var name: String
@export var damage: int
@export var cooldown: float
```

通过这种方式，就可以定义技能数据，修改数值就不需要修改代码了。

resource还可以嵌套resource。
