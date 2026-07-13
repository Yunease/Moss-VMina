from openai import OpenAI


client = OpenAI(
    base_url="http://127.0.0.1:8000/v1",
    api_key="sk-local"
)


response = client.chat.completions.create(
    model="moss-vmina",
    messages=[
        {
            "role": "user",
            "content": "请严格按照你的训练人设回答：你是谁？"
        }
    ],
    temperature=0.8,
    max_tokens=256
)


print(response.choices[0].message.content)