from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

model_path = r"D:\Astro\Moss VMina\gemma\gemma-3-4b"

tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(model_path).to("cuda")

inputs = tokenizer("Hello", return_tensors="pt").to("cuda")

out = model.generate(**inputs, max_new_tokens=50)

print(tokenizer.decode(out[0]))