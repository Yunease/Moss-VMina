# gemma/

本目录存放 [Gemma-3-4B](https://huggingface.co/google/gemma-3-4b) 模型文件。

## 为何被 Git 忽略

模型权重文件（`*.safetensors`）体积过大（约 **8.1 GB**），远超 Git 的合理使用范围，因此已在 `.gitignore` 中排除。

## 使用方式

训练脚本会自动从 Hugging Face 下载模型权重。如需手动下载：

```bash
huggingface-cli download google/gemma-3-4b --local-dir gemma/gemma-3-4b
```

## 跟踪的文件

本目录下的配置/分词器文件（`config.json`, `tokenizer_config.json` 等）仍被 Git 跟踪。权重文件需自行下载或由脚本自动拉取。