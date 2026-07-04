---
title: JavaScript Day3
tags: [Java, JavaScript]
category: 学习
published: 2024-01-30T15:16:51
---

数组就是储存一组数据用的:

关键字: arr

Let arr = [‘1’,’2’]

使用:

Console.log(arr[2])

索引号是从零开始的.数组的遍历就是从索引号0到最后.

Br可以换行

呃呃呃感觉好简单啊

声明数组:

Let arr = [1,2,3,’a’,true]  可以储存任意类型.(let 数组名)

Let arr = new Array(1,2,3,4)

两种方式

遍历数组:

For(let I = 0 ; I < arr.length ; i++ )

{

Doucument.write(arr[i])

}

数组增删改查:

增删略  下标+赋值

新增:

数组名.push()  方法将一个元素或多个元素添加到数组的末尾,并返回数组的新长度

用法:  arr.push(元素1,元素2,元素3)

数组名.unshift()  将一个元素或多个元素添加到数组开头并返回长度

let arr = [1,2,3,4,5,6,7,8,9,12,13,123,23,42,434,4345]

let newarr = []

for( let i = 0,j = 0 ; i < arr.length ; i++ )

{

if ( arr[i] >= 10 )

{

newarr.push(arr[i])

}

}

数组删除:

Arr.pop 删除数组的最后一个元素

Arr.shift 删除数组的第一个元素

Arr.Splice 删除指定的元素,其用法为:

Arr.splice(起始位置,删除几个元素)

例如:

Arr.splice(0,arr.lenth)   //删除全部数组

Arr.splice(1,1)  //从第二个元素开始删除,删除一个

冒泡排序:

简单,不多说了.

Arr.sort()  排序,可以直接排序好一个数组.

升序降序返回:

Arr.sort(function(a,b))

Return a-b

升序返回

Arr.sort(function(a,b))

Return b-a

降序返回

Sort函数  ->  排序

