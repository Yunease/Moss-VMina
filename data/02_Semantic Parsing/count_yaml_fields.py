import os
import glob
import yaml

root = r'D:/Astro/Moss VMina/data/02_Semantic Parsing'
files = glob.glob(os.path.join(root, '**', '*.md'), recursive=True)

print(f'Total markdown files: {len(files)}')

all_fields = {}
yaml_count = 0

for f in files:
    with open(f, 'r', encoding='utf-8', errors='ignore') as fh:
        content = fh.read(5000)

    if content.startswith('---'):
        end = content.find('---', 3)
        if end != -1:
            yaml_text = content[3:end].strip()
            yaml_count += 1
            try:
                data = yaml.safe_load(yaml_text)
                if isinstance(data, dict):
                    for key in data:
                        all_fields[key] = all_fields.get(key, 0) + 1
            except yaml.YAMLError:
                pass

print(f'\nFiles with YAML front matter: {yaml_count}')
print(f'\nAll fields (sorted by frequency):')
for k, v in sorted(all_fields.items(), key=lambda x: -x[1]):
    print(f'  {k}: {v}')

print(f'\nTotal unique fields: {len(all_fields)}')
print(f'Total field occurrences: {sum(all_fields.values())}')