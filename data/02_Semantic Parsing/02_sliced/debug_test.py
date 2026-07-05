import re
text = open('D:/Astro/Moss VMina/data/01_raw/external/2.md', encoding='utf-8').read()
print(f'总字数: {len(text)}')
print(f'去掉首尾空格: {len(text.strip())}')

pat = re.compile(r'(?:[。？！…]|\.{3,}|……)[）」"\']?|[）」"\'](?=[\s\n\r]|$)')
for m in pat.finditer(text[:400]):
    print(f'  句尾: pos={m.end()}, match={repr(m.group())}')