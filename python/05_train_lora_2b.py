#!/usr/bin/env python3
"""
Qwen3.5-2B LoRA QLoRA SFT训练

训练数据格式:
jsonl:
{
    "instruction": "...",
    "output": "..."
}

"""

import json
import random
import torch
import numpy as np

from pathlib import Path
from torch.utils.data import Dataset

from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
    set_seed,
)

from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training,
)


# =========================
# 路径
# =========================

MODEL_PATH = r"D:\Astro\Moss VMina\qwen\Qwen--Qwen3.5-2B"

TRAIN_PATH = r"D:\Astro\Moss VMina\data\07_train_test_2_spilt\merged_train.jsonl"

VAL_PATH = r"D:\Astro\Moss VMina\data\06_train_test_split\val.jsonl"

OUTPUT_DIR = r"D:\Astro\Moss VMina\output\lora_qwen3.5_2b"


# =========================
# 超参数
# =========================

SEED = 42


# LoRA
LORA_R = 32
LORA_ALPHA = 64
LORA_DROPOUT = 0.1


TARGET_MODULES = [
    "q_proj",
    "k_proj",
    "v_proj",
    "o_proj",

    "gate_proj",
    "up_proj",
    "down_proj",
]


# 数据
MAX_LENGTH = 512


# 训练
NUM_EPOCHS = 2

BATCH_SIZE = 1

GRADIENT_ACCUMULATION = 4


LEARNING_RATE = 5e-5

WEIGHT_DECAY = 0.01


LR_SCHEDULER_TYPE = "cosine"

WARMUP_RATIO = 0.03


EVAL_STEPS = 100

LOG_STEPS = 10

SAVE_STEPS = 200



SYSTEM_PROMPT = """
你是Moss VMina，琴泠的朋友。
你温柔、活泼、有自己的想法。
你喜欢和用户聊天，也擅长帮助用户解决问题。
""".strip()



# =========================
# Dataset
# =========================

class SFTDataset(Dataset):

    def __init__(
        self,
        path,
        tokenizer,
        max_length=MAX_LENGTH
    ):

        self.tokenizer = tokenizer
        self.max_length = max_length

        self.data = []


        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:

            for line_no,line in enumerate(f,1):

                line=line.strip()

                if not line:
                    continue

                item=json.loads(line)


                if (
                    "instruction" not in item
                    or
                    "output" not in item
                ):
                    raise ValueError(
                        f"{path}:{line_no} 缺少字段"
                    )


                self.data.append(item)



        print(
            f"Loaded {len(self.data)} samples from {path}"
        )


        self.sanity_check()



    def __len__(self):

        return len(self.data)



    def build_ids(self,index):

        item=self.data[index]


        messages=[

            {
                "role":"system",
                "content":SYSTEM_PROMPT
            },

            {
                "role":"user",
                "content":item["instruction"]
            }

        ]



        prompt_ids=self.tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
        )


        if hasattr(prompt_ids,"input_ids"):
            prompt_ids=prompt_ids["input_ids"]



        answer_ids=self.tokenizer(
            item["output"],
            add_special_tokens=False
        )["input_ids"]



        if len(answer_ids)>=self.max_length:

            answer_ids=answer_ids[:self.max_length]

            prompt_ids=[]


        elif len(prompt_ids)+len(answer_ids)>self.max_length:

            keep_prompt=self.max_length-len(answer_ids)

            prompt_ids=prompt_ids[-keep_prompt:]



        input_ids=prompt_ids+answer_ids


        labels=[
            -100
        ]*len(prompt_ids)+answer_ids



        return (
            input_ids,
            labels,
            len(prompt_ids)
        )



    def sanity_check(self):

        print("[Sanity check]")


        for i in range(
            min(3,len(self.data))
        ):

            ids,labels,prompt_len=self.build_ids(i)


            loss_ids=[
                x
                for x,y in zip(ids,labels)
                if y!=-100
            ]


            text=self.tokenizer.decode(
                loss_ids,
                skip_special_tokens=False
            )


            print(
                f"{i}: prompt={prompt_len}"
            )

            print(
                text[:100]
            )

            print()



    def __getitem__(self,index):

        ids,labels,_=self.build_ids(index)


        return {

            "input_ids":ids,

            "attention_mask":[1]*len(ids),

            "labels":labels

        }



# =========================
# Main
# =========================


def main():


    print("="*60)

    print(
        " Qwen3.5-2B QLoRA SFT Training "
    )

    print("="*60)



    set_seed(SEED)

    random.seed(SEED)

    np.random.seed(SEED)



    if not torch.cuda.is_available():

        raise RuntimeError(
            "需要CUDA GPU"
        )



    gpu=torch.cuda.get_device_name(0)

    vram=(
        torch.cuda.get_device_properties(0)
        .total_memory
        /
        1024**3
    )


    print(
        f"GPU: {gpu} {vram:.1f}GB"
    )



    bf16=torch.cuda.is_bf16_supported()


    dtype=(
        torch.bfloat16
        if bf16
        else torch.float16
    )



    Path(OUTPUT_DIR).mkdir(
        parents=True,
        exist_ok=True
    )



    # tokenizer

    print(
        "[1] tokenizer"
    )


    tokenizer=AutoTokenizer.from_pretrained(
        MODEL_PATH,
        trust_remote_code=True
    )


    if tokenizer.pad_token is None:

        tokenizer.pad_token=tokenizer.eos_token



    tokenizer.padding_side="right"



    # dataset

    print(
        "[2] dataset"
    )


    train_dataset=SFTDataset(
        TRAIN_PATH,
        tokenizer
    )


    val_dataset=SFTDataset(
        VAL_PATH,
        tokenizer
    )



    # quant

    print(
        "[3] quant"
    )


    bnb_config=BitsAndBytesConfig(

        load_in_4bit=True,

        bnb_4bit_quant_type="nf4",

        bnb_4bit_compute_dtype=dtype,

        bnb_4bit_use_double_quant=True

    )



    # model


    print(
        "[4] model"
    )


    model=AutoModelForCausalLM.from_pretrained(

        MODEL_PATH,

        quantization_config=bnb_config,

        device_map="auto",

        trust_remote_code=True,

        torch_dtype=dtype

    )



    model.config.use_cache=False


    model=prepare_model_for_kbit_training(
        model
    )


    model.gradient_checkpointing_enable()



    # lora


    print(
        "[5] LoRA"
    )


    config=LoraConfig(

        r=LORA_R,

        lora_alpha=LORA_ALPHA,

        target_modules=TARGET_MODULES,

        lora_dropout=LORA_DROPOUT,

        bias="none",

        task_type="CAUSAL_LM"

    )


    model=get_peft_model(
        model,
        config
    )


    model.print_trainable_parameters()



    # trainer


    print(
        "[6] train"
    )


    args=TrainingArguments(

        output_dir=OUTPUT_DIR,

        per_device_train_batch_size=BATCH_SIZE,

        per_device_eval_batch_size=1,

        gradient_accumulation_steps=GRADIENT_ACCUMULATION,

        num_train_epochs=NUM_EPOCHS,


        learning_rate=LEARNING_RATE,

        weight_decay=WEIGHT_DECAY,


        lr_scheduler_type=LR_SCHEDULER_TYPE,


        warmup_ratio=WARMUP_RATIO,


        bf16=bf16,

        fp16=not bf16,


        logging_steps=LOG_STEPS,


        eval_strategy="steps",

        eval_steps=EVAL_STEPS,


        save_strategy="steps",

        save_steps=SAVE_STEPS,


        save_total_limit=2,


        remove_unused_columns=False,


        report_to="none",


        gradient_checkpointing=True,


        optim="adamw_8bit",


        load_best_model_at_end=True,


        metric_for_best_model="eval_loss",

        greater_is_better=False,

    )



    trainer=Trainer(

        model=model,

        args=args,

        train_dataset=train_dataset,

        eval_dataset=val_dataset,

        processing_class=tokenizer,


        data_collator=DataCollatorForLanguageModeling(

            tokenizer,

            mlm=False

        )

    )



    trainer.train()



    print(
        "保存LoRA..."
    )


    trainer.save_model(
        OUTPUT_DIR
    )


    tokenizer.save_pretrained(
        OUTPUT_DIR
    )


    print(
        "完成"
    )



if __name__=="__main__":

    main()