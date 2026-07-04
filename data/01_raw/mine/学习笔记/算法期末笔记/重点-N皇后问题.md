---
title: 重点-N皇后问题
tags: [算法]
category: 学习
published: 2026-01-15T21:13:59
---

输入k个皇后，输出满足的情况：

NQueens(k)

{

If k > n then

Output x //如果此时已经进行到最后一行，相当于找到一个可行解

For col = 1 to n do //尝试在每一行放皇后

{

If Place(k,col) then  //检验是否可以放下

{

X[k] <- col   //在k行col列 放置皇后

NQueens（k+1）  //递归到下一行

}

}

}

验证函数：

Place(k,col)

{

For I = 1 to k – 1 do

{

If x[i] == col then

Return false

If x[i] – I == col – k then

Return false

If x[i] + I == col + k then

Return false

}

Return true

}

