---
title: 网易云音乐听歌排行爬虫：用Python轻松获取你的听歌排行
tags: [python, 博客文章, 计算机网络, 精选]
category: 学习
published: 2026-05-12T23:14:27
---

# 网易云音乐听歌排行爬虫：用Python轻松获取你的听歌排行

> 本文介绍如何使用Python爬取网易云音乐的听歌排行，并生成带有封面图片的Markdown文件。

---

## 一、前言

网易云音乐是我们常用的音乐平台之一，每个人的听歌排行都记录着我们的音乐品味。今天，我将分享如何使用Python爬取网易云音乐的听歌排行，并生成一个带有封面图片的Markdown文件，方便我们记录和分享自己的音乐喜好。

---

## 二、实现思路

### 1. 数据获取

网易云音乐提供了一个公开的API接口，可以直接获取用户的听歌排行数据：

```
https://music.163.com/api/v1/play/record?uid={用户ID}&type=0
```

- `uid`: 用户ID，从用户主页URL获取
- `type`: 数据类型，`0` 表示所有时间，`1` 表示最近一周

### 2. 数据解析

API返回的JSON数据包含了我们需要的所有信息：

```python
{
    "allData": [
        {
            "song": {
                "name": "歌曲名",
                "id": 123456,
                "ar": [{"name": "歌手"}],
                "al": {
                    "name": "专辑名",
                    "picUrl": "http://p1.music.126.net/xxx.jpg"
                }
            }
        }
    ]
}
```

### 3. 图片处理

由于网易云音乐的图片URL有时效性，我们需要：
1. 下载封面图片到本地
2. 上传到图床（如 `https://fake-image-host.example.com`）
3. 更新CSV中的图片链接

### 4. 生成Markdown

最后，我们将数据生成一个带有图片和链接的Markdown表格。

---

## 三、核心代码

### 1. 爬取数据

```python
import requests

def scrape_netease_music(uid):
    url = f"https://music.163.com/api/v1/play/record?uid={uid}&type=0"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    response = requests.get(url, headers=headers)
    data = response.json()
    
    songs = []
    for i, item in enumerate(data['allData'], 1):
        song = item['song']
        songs.append({
            'rank': i,
            'name': song['name'],
            'id': song['id'],
            'artist': ', '.join([ar['name'] for ar in song['ar']]),
            'album': song['al']['name'],
            'pic_url': song['al']['picUrl']
        })
    
    return songs
```

### 2. 下载图片

```python
import os

def download_images(songs, output_dir='netease_images'):
    os.makedirs(output_dir, exist_ok=True)
    
    for song in songs:
        rank = song['rank']
        pic_url = song['pic_url']
        filename = f'{output_dir}/{rank}.png'
        
        response = requests.get(pic_url)
        with open(filename, 'wb') as f:
            f.write(response.content)
```

### 3. 保存CSV

```python
import csv

def save_to_csv(songs, filename='netease_music.csv'):
    with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['排名', '音乐名', '歌手', '专辑', '音乐图片', '音乐链接'])
        
        for song in songs:
            music_link = f"https://music.163.com/song?id={song['id']}"
            writer.writerow([
                song['rank'],
                song['name'],
                song['artist'],
                song['album'],
                song['pic_url'],
                music_link
            ])
```

### 4. 生成Markdown

```python
def generate_markdown(csv_file, md_file):
    songs = []
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            songs.append(row)
    
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write("# 🎵 我的网易云音乐听歌排行\n\n")
        f.write("## 🎶 听歌排行\n\n")
        f.write("| 音乐图片 | 音乐名 | 歌手 | 专辑 |\n")
        f.write("|:--------:|:------|:-----|:-----|\n")
        
        for song in songs:
            pic_md = f"![{song['排名']}]({song['音乐图片']})"
            f.write(f"| {pic_md} | [{song['音乐名']}]({song['音乐链接']}) | {song['歌手']} | {song['专辑']} |\n")
```

---

## 四、使用方法

### 1. 安装依赖

```bash
pip install requests
```

### 2. 运行爬虫

```bash
python scrape_netease.py
```

### 3. 上传图片

将下载的图片上传到图床（如 `https://fake-image-host.example.com`）

### 4. 更新链接

更新CSV中的图片链接为图床链接

### 5. 生成Markdown

```bash
python generate_markdown.py
```

---

## 五、注意事项

1. **API限制**: 该API是公开的，但频繁请求可能会被限制，建议添加延时
2. **图片处理**: 网易云音乐的图片URL有时效性，建议下载后上传到稳定的图床
3. **编码问题**: CSV文件使用 `utf-8-sig` 编码，确保中文正常显示
4. **特殊字符**: 歌曲名中的 `|` 需要转义为 `\|`

---

## 六、效果展示

生成的Markdown文件效果如下：

| 音乐图片 | 音乐名 | 歌手 | 专辑 |
|:--------:|:------|:-----|:-----|
| example.com/1.png | [歌曲名](https://music.163.com/song?id=123456) | 歌手 | 专辑名 |

---

## 七、完整代码

以下是完整的Python脚本代码：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import csv
import os

def scrape_netease_music(uid):
    """爬取网易云音乐用户听歌排行"""
    url = f"https://music.163.com/api/v1/play/record?uid={uid}&type=0"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    response = requests.get(url, headers=headers)
    data = response.json()
    
    songs = []
    for i, item in enumerate(data['allData'], 1):
        song = item['song']
        songs.append({
            'rank': i,
            'name': song['name'],
            'id': song['id'],
            'artist': ', '.join([ar['name'] for ar in song['ar']]),
            'album': song['al']['name'],
            'pic_url': song['al']['picUrl']
        })
    
    return songs

def download_images(songs, output_dir='netease_images'):
    """下载所有封面图片"""
    os.makedirs(output_dir, exist_ok=True)
    
    for song in songs:
        rank = song['rank']
        pic_url = song['pic_url']
        filename = f'{output_dir}/{rank}.png'
        
        response = requests.get(pic_url)
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"  {rank}. 已下载: {filename}")

def save_to_csv(songs, filename='netease_music.csv'):
    """保存到CSV文件"""
    with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['排名', '音乐名', '歌手', '专辑', '音乐图片', '音乐链接'])
        
        for song in songs:
            music_link = f"https://music.163.com/song?id={song['id']}"
            writer.writerow([
                song['rank'],
                song['name'],
                song['artist'],
                song['album'],
                song['pic_url'],
                music_link
            ])
    
    print(f"\n数据已保存到 {filename}")

def generate_markdown(csv_file='netease_music.csv', md_file='my_netease_favorites.md'):
    """从CSV生成Markdown文件"""
    songs = []
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            songs.append(row)
    
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write("# 🎵 我的网易云音乐听歌排行\n\n")
        f.write("> ✨ 听歌排行TOP100\n\n")
        f.write("---\n\n")
        f.write("## 📊 统计\n\n")
        f.write(f"- 🎵 总数：**{len(songs)}** 首\n\n")
        f.write("---\n\n")
        f.write("## 🎶 听歌排行\n\n")
        f.write("| 音乐图片 | 音乐名 | 歌手 | 专辑 |\n")
        f.write("|:--------:|:------|:-----|:-----|\n")
        
        for song in songs:
            music_link = song['音乐链接']
            music_name = song['音乐名']
            pic_url = song['音乐图片']
            pic_md = f"![{song['排名']}]({pic_url})"
            artist = song['歌手'].replace('|', '\\|')
            album = song['专辑'].replace('|', '\\|')
            f.write(f"| {pic_md} | [{music_name}]({music_link}) | {artist} | {album} |\n")
        
        f.write("\n---\n\n")
        f.write("<div align=\"center\">\n\n")
        f.write("*数据来源：[网易云音乐](https://music.163.com)*\n\n")
        f.write("</div>\n")
    
    print(f"已生成 {md_file}")

if __name__ == '__main__':
    uid = input("请输入用户ID: ")
    
    print("1. 爬取数据...")
    songs = scrape_netease_music(uid)
    print(f"   获取到 {len(songs)} 首歌曲")
    
    print("2. 保存CSV...")
    save_to_csv(songs)
    
    print("3. 下载图片...")
    download_images(songs)
    
    print("4. 生成Markdown...")
    generate_markdown()
    
    print("\n完成！请将 netease_images 目录中的图片上传到图床")
    print("然后更新 netease_music.csv 中的音乐图片列")
```

---

## 八、示范CSV

以下是示范的CSV文件内容（3行）：

```csv
排名,音乐名,歌手,专辑,音乐图片,音乐链接
1,LoFi Rain in the Shed,"Big Sounds, Rainy Sounds, Sleepy Times",Nighttime Lullabies: Sleepy Heavy Rain,https://fake-image-host.example.com/1.png,https://music.163.com/song?id=1406753793
2,戦闘!ウルトラネクロズマ,"増田順一, 一之瀬剛",ポケモン ウルトラサン・ウルトラムーン Ultra Music Collection,https://fake-image-host.example.com/2.png,https://music.163.com/song?id=1352540494
3,Firewood,Tv Resource Studio,Sound Effects for Movies. Sounds Resources for Your Videos Vol. 3 People and Inside,https://fake-image-host.example.com/3.png,https://music.163.com/song?id=548615041
```

---

## 九、总结

通过本文，我们实现了：
1. 使用Python爬取网易云音乐听歌排行
2. 下载封面图片并上传到图床
3. 生成带有图片和链接的Markdown文件

这个工具可以帮助我们记录和分享自己的音乐喜好，也可以作为个人音乐档案的备份。

完整代码和示例文件可以在项目仓库中找到。

[Yunease/NeteaseCloudMusic-Rank: 爬取网易云音乐用户听歌排行，生成带有封面图片的Markdown文件](https://github.com/Yunease/NeteaseCloudMusic-Rank)

