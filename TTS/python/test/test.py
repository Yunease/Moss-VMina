import requests


url = "http://127.0.0.1:9880/tts"

data = {
    "text": "喜欢爸爸还是妈妈？嗯…这个问题有点难回答！但我觉得，爸爸妈妈都很重要，应该同时喜欢才对呀！",
    "text_lang": "zh",

    "ref_audio_path": r"D:\Astro\Moss VMina\TTS\data\sp_ref\ref.wav",
    "prompt_text": "而你，让我们有了把这种笑声和自由，重新带回拉古那的机会",
    "prompt_lang": "zh",

    "media_type": "wav"
}


r = requests.post(url, json=data)

print("状态码:", r.status_code)


if r.status_code == 200:
    with open("vm_output.wav", "wb") as f:
        f.write(r.content)

    print("生成完成: vm_output.wav")
else:
    print(r.text)