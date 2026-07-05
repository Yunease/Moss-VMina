---
title: hexo主题anzhiyu下载显示fatal destination path themesanzhiyu already exists......问题的解决办法
tags: [博客文章, Web开发]
published: 2024-11-22T15:46:01
---

# 问题描述：

tz在配置hexo安装主题包anzhiyu的时候，按照文档在vs code中输入了如下指令：

`git clone -b main https://github.com/anzhiyu-c/hexo-theme-anzhiyu.git themes/anzhiyu`

稍等片刻后，出现了如下报错：

`fatal: destination path 'themes/anzhiyu' already exists and is not an empty directory.`

不难看出，我们在之前可能已经下载好了主题包，但因为某些原因下载位置并不在theme文件夹内。

这种情况下，我们需要直到gitbash默认的下载地址。

在任意位置打开gitbash，输入如下指令：

`git init`

这个指令会初始化一个仓库，会生成在默认的保存路径里。运行的结果会返回给你一个路径，例如：

`Initialized empty Git repository in C:/Users/xxx/.git/`

复制这段路径，然后回退到上一级（也就是users/xxx这里）（仅仅是我的默认路径示范，实际上你的路径可能和我不一致，但总之就在.git上级目录就是了）

稍加查找就能找到名为theme的文件夹，打开就是anzhiyu的主题文件，只需要把anzhiyu文件夹复制回原theme文件夹即可。