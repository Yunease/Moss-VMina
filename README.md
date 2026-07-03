# Moss VMina - 模型微调项目

基于个人语料数据对 Moss / MiniMax 等大语言模型进行微调（SFT/QLoRA）的训练项目。

## 项目结构

```
├── config/                  # 训练配置文件
├── data/
│   ├── raw/                 # 原始语料素材
│   │   ├── mine/            # 个人原始数据
│   │   └── external/        # 外部来源数据
│   └── processed/           # 清洗后的数据
│       └── mine/            # 清洗后的个人数据
├── python/                  # Python 工具模块
├── scripts/
│   └── data_cleaning/       # 数据清洗脚本
└── README.md
```

## 处理流程

1. 收集原始语料 → `data/raw/`
2. 数据清洗（去重、格式化）→ `data/processed/`
3. 构建训练集 → 模型微调