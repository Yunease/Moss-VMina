import json

path = r"D:\Astro\Moss VMina\data\07_train_test_3_spilt\train.jsonl"

with open(path,"r",encoding="utf-8") as f:
    for i,line in enumerate(f):
        try:
            json.loads(line)
        except Exception as e:
            print("错误行:", i+1)
            print(line[:300])
            print(e)
            break