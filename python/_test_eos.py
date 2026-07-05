from transformers import AutoTokenizer

tok = AutoTokenizer.from_pretrained('D:/Astro/Moss VMina/qwen/Qwen3.5-0.8B', trust_remote_code=True)

text = 'hello world'
r1 = tok(text, add_special_tokens=True)
r2 = tok(text, add_special_tokens=False)
print('=== Simple text ===')
print(f'True : {r1}')
print(f'False: {r2}')

full = tok.apply_chat_template(
    [{'role': 'user', 'content': 'hi'}, {'role': 'assistant', 'content': 'there'}],
    tokenize=False, add_generation_prompt=False
)
print(f'\nTemplate text: {full!r}')
print(f'Template end: ...{full[-30:]!r}')

r3 = tok(full, add_special_tokens=True)
r4 = tok(full, add_special_tokens=False)
print(f'True({len(r3["input_ids"])}): {r3["input_ids"]}')
print(f'False({len(r4["input_ids"])}): {r4["input_ids"]}')

if len(r3['input_ids']) != len(r4['input_ids']):
    extra = r3['input_ids'][len(r4['input_ids']):]
    print(f'Extra tokens: {extra} -> {tok.decode(extra)!r}')
else:
    match = all(a == b for a, b in zip(r3['input_ids'], r4['input_ids']))
    print(f'Exact same token IDs: {match}')
    if not match:
        for i in range(min(len(r3['input_ids']), len(r4['input_ids']))):
            if r3['input_ids'][i] != r4['input_ids'][i]:
                print(f'Diff at pos {i}: True={r3["input_ids"][i]}, False={r4["input_ids"][i]}')
                break