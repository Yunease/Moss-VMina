---
title: 脚本标签label和流程控制
published: 2026-02-21T16:06:01
tags: [博客文章]
category: '开发日志'
---

大家早上好中午好晚上好哦！小琴现在开心极了，那么我们快一些开始吧！



# label语句



label语句允许使用一个自定义的标签声明一个程序点位，有点类似goto语句，允许使用在renpy中，也可以使用在python里。

```renpy
label sample1:
    "这是一个'sample1'脚本标签。"

label sample2(a="default"):
    "这是一个'sample2'脚本标签。"
    "a = [a]"
```

一个label语句可能只跟某一个语句块(block)关联。 这种情况下，主控流程遇到label语句就会进入语句块，并顺序执行之后的语句，直到运行到结尾： 下面的样例代码，在跳转到“origin”标签之后，会依次产生“a、b、c”。

```renpy
label origin:
"a"
label hasblock:
    "b"
"c"
return
```

总共有两种脚本标签(label)：*global* 和 *local* 。global标签存储在global命名空间中，整个项目中应该具有唯一性，即全局性，可以在任意位置调用使用。 local标签可以同名，但需要与不同的global标签做关联。 需要声明一个local标签的话，在标签名前缀一个英文句号“.”即可。例如：

```renpy
label global_label:
    "这在一个global脚本标签里。"
label .local_label:
    ".这里属于local脚本标签。"
    jump .another_local
label .another_local:
    "另一个local脚本标签"
    jump .local_label
```

local脚本标签在关联的global标签内部可以直接引用。其他地方则需要使用标签全名，由关联的globle标签和local标签组成。 一个关于global标签和local标签的例子如下：

```renpy
label another_global:
    "现在让我们跳转进入其他地方的local脚本标签。"
    jump global_label.local_name
```

lable语句可以带一些可选参数。这些参数的处理机制在 [**PEP 570**](https://peps.python.org/pep-0570/) 中有详细说明，这里仅说两种例外:

第一，默认参数的值会在调用时才进行计算。

第二，变量具有动态声明周期。某个变量从标签参数获取值后，若出现return语句则会恢复原值。 使用某个变量指定语句后，该变量可能会也可能不会从标签参数获取值，具体取决于脚本中的语句。 这与纯Python代码不同。

```renpy
default a = 3

label start:
    menu:
        "调用":
            call label_with_params(5)
        "跳转":
            jump label_without_params
    jump start

label label_with_params(a):
label label_without_params:
    e "a = [a]" # 显示5还是3，取决于通过何种路径执行到这里
    return
```

仅仅通过jump语句还是从上一条语句顺序执行这点信息，往往并不能完全判断出标签中变量的值。 对于标签变量的样例，请参考 [call语句](https://doc.renpy.cn/zh-CN/label.html#call-statement)。

如果某个变量具有动态生命周期，它的值会持续到其所属的label标签中出现一个return语句为止。 尝试使用jump或previous语句传递该变量的值都是不明智的。 带有参数的label样例，详见 [call语句](https://doc.renpy.cn/zh-CN/label.html#call-statement) 。



## jump语句



jump语句用于将主控流程转入指定的脚本标签(label)处。

若出现了 `expression` (表达式)关键词，关键词后面的表达式将被赋值，而被计算后的对应字符串则会被用作跳转目标的标签语句。若未出现 `expression` (表达式)关键词，跳转目标的标签名字就必须精确指定。

与call语句不同，jump语句不会将下一个语句放入栈(stack)中。因此，执行完跳转标签对应的语句块之后，主控流程不会回到跳转前的脚本位置。

```renpy
label loop_start:

    e "哦，不！看起来我们陷入了一个无限循环之中。"

    jump loop_start
```



## call语句



call语句用于将主控流程转入给定的脚本标签(label)处。call语句会将下一条语句压入到调用栈(stack)中，并允许主控流程在执行完这次调用后，回到调用发生的脚本位置。

若出现了 `expression` 关键词，将计算关键词后面的表达式，而计算得到的字符串则会被用作跳转目标的标签语句。若未出现 `expression` 关键词，跳转目标的标签名字就必须显式指定。

`from` 分句是可选的，在label语句后面直接添加入参名和值，并直接在该label下直接使用。一个命名直白的标签(lable)有助于我们能利用栈(stack)回到脚本里合适的地方，就算加载的是修改过的脚本。

call语句可以使用参数，详见 [**PEP 448**](https://peps.python.org/pep-0448/)。

当我们使用一个带入参列表的调用表达式时，必须在表达式和入参列表之间插入关键词 `pass` 。 否则，入参列表会被当作表达式的一部分，而不是call语句的一部分。

```
label start:

    e "首先，我们调用一个支线。"

    call subroutine

    call subroutine(2)

    call expression "sub" + "routine" pass (count=3)

    return

label subroutine(count=1):

    e "我来过这里 [count] 次了。"
    e "接着，我们会从支线返回。"

    return
```



### 关键执行逻辑拆解



1. 进入`label start`后，先执行固定台词`e "首先，我们调用一个支线。"`；

2. **第一次调用`call subroutine`**：无传参，使用`subroutine`的默认参数`count=1`，执行对应台词后`return`回到`start`；

3. **第二次调用`call subroutine(2)`**：显式传参`count=2`，覆盖默认值，执行台词后`return`回到`start`；

4. 第三次调用`call expression "sub"+"routine" pass (count=3)`

   ：

   - `expression`后计算字符串拼接结果为`subroutine`，确定调用目标；
   - `pass (count=3)`为目标标签传参`count=3`，执行台词后`return`回到`start`；

   

5. 最后执行`start`的`return`，结束该标签的执行。

Warning

> 每条 `call` 语句后面都不加上 `from` 从句就发布游戏是危险的。当然也可以通过发布更新补丁解决。 在没有 `from` 从句的情况下，编辑 `call` 相关的脚本，可能会有存档损坏的风险。
>
> 构建发行版时，将选项“向call语句添加from从句”勾选上就能解决以上问题。
>
> 



### pass语句



`pass`仅在**动态调用标签（call expression）** 时使用，作用是**向动态计算出的标签传递参数**。

- 静态调用标签（直接写标签名）：可以直接用`call 标签名(参数)`传参，无需`pass`；
- 动态调用标签（标签名由表达式计算，如字符串拼接、变量取值）：必须用`pass (参数名=值)`传参，这是 Ren'Py 的固定语法。

```renpy
label start:
    e "开始演示pass的用法"
    
    # 1. 静态调用：直接传参，无需pass
    call sub(1)
    
    # 2. 动态调用：标签名由字符串拼接得到，必须用pass传参
    $ target_label = "sub"  # 动态定义要调用的标签名
    call expression target_label pass (count=2)
    
    # 3. 更典型的动态调用：字符串拼接
    call expression "sub" pass (count=3)
    
    e "所有调用完成"
    return

# 被调用的支线标签
label sub(count=0):
    e "我收到的参数是：[count]"
    return
```



### `from`语句：自定义 call 的返回点 / 标记跳转来源



### 核心用途

`from`有两个核心场景，最常用的是**修改 call 的返回逻辑**：

1. **配合 call**（核心）：默认情况下，`call 标签`执行完`return`后会回到`call`的下一行；`from`可以指定`return`后的跳转目标（返回点）；
2. **配合 jump**（辅助）：标记跳转的来源，主要用于调试或复杂流程的溯源（实际开发中用得少）。

### 示例 1：修改 call 的返回点（最常用）

```
label start:
    e "进入start标签，准备调用支线"
    call sub from back_to_here  # 调用sub，并指定return后回到back_to_here标记
    
    # 这个位置默认是return的返回点，但被from修改了，所以不会执行
    e "这行不会被执行"

label back_to_here:  # 自定义的返回点（标记）
    e "我回到了自定义的返回点！"
    return

label sub:
    e "我在支线sub里"
    return  # 执行return时，会跳转到from指定的back_to_here，而非call的下一行
```

### 执行结果（对话顺序）

1. 进入 start 标签，准备调用支线
2. 我在支线 sub 里
3. 我回到了自定义的返回点！

当你使用了from语句，就不会回到默认位置去。



## return语句



return语句会在调用栈中弹出最顶层的那条语句，并将主控流程转到那条语句。若调用栈为空，返回语句将重启Ren’Py，将主控流程切换至主菜单。

若返回语句带有可选项表达式，表达式会被计算求值，并且结果会被存储在_return变量中。_return变量依赖于各种场景动态变化。



## 特殊脚本标签(label)

以下脚本标签(label)会在Ren’Py中使用：

- `start`

  默认情况下，Ren’Py在游戏启动后会跳转至这个标签。这个标签最好不要随便改动。

- `quit`

  若该标签存在，当用户退出游戏时该标签内容会被调用。

- `after_load`

  若该标签存在，当游戏读档后会调用这个标签内容。其可能被用于游戏内容更新后的数据修复。 如果数据从此标签后发生变化，应该调用 [`renpy.block_rollback()`](https://doc.renpy.cn/zh-CN/save_load_rollback.html#renpy.block_rollback) 函数防止用户从该存档点回滚。

- `splashscreen`

  若该标签存在，游戏首次运行时，在主菜单出现前，该标签内容会被调用。 详见 [添加启动画面](https://doc.renpy.cn/zh-CN/splashscreen_presplash.html#adding-a-splashscreen) 。

- `before_main_menu`

  若该标签存在，在主菜单出现前，该标签内容会被调用。在少数情况下，其用来设置主菜单，例如背景播放一段影片。

- `main_menu`

  若该标签存在，标签内容会被调用，用来替代默认的主菜单。若其内容中包含return语句，Ren’Py将从start标签处开始游戏。例如，下面这段脚本在不显示主菜单的情况下开始游戏。`label main_menu:    return `

- `after_warp`

  若该标签存在，则调用warp语句时，此标签至传送(warp)点前的语句都将被执行。详见 [传送至某行](https://doc.renpy.cn/zh-CN/developer_tools.html#warping-to-a-line)

- `hide_windows`

  若该标签存在，当玩家使用鼠标右键或键盘H键隐藏对话窗口时，将调用此标签。 若标签返回值为True，隐藏对话窗口行为将取消(依然当作隐藏已经发生)。否则，继续隐藏对话窗口。

Ren’Py also uses the following labels to show some of the [special screens](https://doc.renpy.cn/zh-CN/screen_special.html): Ren’Py还是用下列标签显示某些 [特殊界面](https://doc.renpy.cn/zh-CN/screen_special.html) ：

- `main_menu_screen`
- `load_screen`
- `save_screen`
- `preferences_screen`
- `joystick_preferences_screen`



## 上下文



上下文(context)是Ren’Py用于管理游戏中可以修改并且可以存档的各种状态值，具体包括：

- 当前Ren’Py运行状态
- 调用栈，已经上面提到的 `renpy.dynamic()` 使用的各种动态变量名和变量值。
- 当前显示的所有图像信息(包括图像属性和用到的各种变换等)
- 当前显示的界面和界面中的各种变量
- 正在播放或在播放队列中的音频

大多数时候游戏中仅有一个上下文，上下文中的各项也仅存在一个实例。 进入主菜单或游戏内菜单时，上下文中的各项可能会改变，但在离开菜单后各项会恢复。 其中一些改变是自动处理的，比如screen图层在上下文内容变化时会清空。

使用 [回放](https://doc.renpy.cn/zh-CN/rooms.html#replay) 功能和 [`隐藏UI`](https://doc.renpy.cn/zh-CN/screen_actions.html#HideInterface) 函数时，Ren’Py会创建新的上下文。

[界面语言](https://doc.renpy.cn/zh-CN/screens.html#screens) 的创立，很大程度上就是为了减少频繁创建上下文。

仅在基本上下文(即仅有一个上下文时的那个)中才能使用回滚(rollback)。也只有基本上下文才可以存档，这是游戏菜单会用到上下文。

- renpy.call_in_new_context(*label*, **args*, ***kwargs*)[link](https://doc.renpy.cn/zh-CN/label.html#renpy.call_in_new_context)

  该函数创建一个新的上下文(context)，并从这个上下文(context)中给定的脚本标签(label)处开始执行Ren’Py脚本。新的上下文(context)中禁用了回滚功能，并且存档/读档会发生在顶层的上下文(context)中。使用该函数可以在原有交互中启动第二层交互。

- renpy.context()[link](https://doc.renpy.cn/zh-CN/label.html#renpy.context)

  返回一个唯一对象，指向当前上下文。进入某个新的上下文时，该对象也将被赋值为新的上下文。但对该对象的修改不会影响其指向的原上下文内容。该对象可以存档，并参与回滚操作。

- context_dynamic(**variables*)[link](https://doc.renpy.cn/zh-CN/label.html#context_dynamic)

  该函数可以将若干个变量名作为入参，并根据当前上下文调整这些变量。当返回前一个上下文后，变量的值会恢复为该函数调用之前的值。[命名存储空间](https://doc.renpy.cn/zh-CN/python.html#named-stores) 中的变量都可以支持。调用样例如下：`$ renpy.context_dynamic("x", "y", "z") $ renpy.context_dynamic("mystore.serial_number") `

- renpy.context_nesting_level()[link](https://doc.renpy.cn/zh-CN/label.html#renpy.context_nesting_level)

  返回当前上下文的嵌套层级(nesting level)。 最外层的上下文的层级为0(该层上下文可以存档、读档和回滚)。其他上下文的嵌套曾经都不是0，比如菜单和回放的上下文。

- renpy.invoke_in_new_context(*callable*, **args*, ***kwargs*)[link](https://doc.renpy.cn/zh-CN/label.html#renpy.invoke_in_new_context)

  该函数创建了一个新的上下文(context)，并在上下文(context)中显示调用时指定的python可调用内容(通常是函数)。当函数返回值或者抛出异常时，主控流程会返回到原来的上下文(context)。当我们在同一个句柄(handle)中向玩家展示一些信息(比如确认提示)，就可以调用这个函数。其他额外入参都将传给callable处理。该函数创建的上下文无法执行Ren’Py脚本。能改变Ren’Py脚本执行流程的函数，比如 `renpy.jump`都会由外层的上下文处理。 如果想要调用Ren'Py脚本而不是Python函数，需要改用 :func:`renpy.call_in_new_context()`.

- renpy.jump_out_of_context(*label*)[link](https://doc.renpy.cn/zh-CN/label.html#renpy.jump_out_of_context)

  调用该函数会使主控流程离开当前上下文(context)，并转换到父层上下文(context)中指定的脚本标签(label)处。

- renpy.reset_all_contexts()[link](https://doc.renpy.cn/zh-CN/label.html#renpy.reset_all_contexts)

  该函数会上下文栈中的所有元素都弹出(pop off)，恢复所有动态变量的值。完成以上内容后，再创建一个新的上下文。 当前语句结束，游戏从下一条语句继续执行。遇到异常的数据或起始点时，这样做能将Ren’Py设置为初始状态。该函数可用于重置游戏内的一切——包括显示的图像、播放的音乐等，就像游戏刚开始运行。由于该函数会重置Ren’Py，当前语句会立刻结束。该函数设计用在after_load脚本标签后面，可以将游戏的状态数据重置为初始值。接着游戏可以重新绘制场景、播放音乐等，最后跳转到目标脚本标签并继续。
