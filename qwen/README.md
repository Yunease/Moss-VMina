# qwen/

本目录存放 [Qwen3.5-0.8B](https://huggingface.co/Qwen/Qwen3.5-0.8B) 模型文件。

## 为何被 Git 忽略

模型权重文件（`*.safetensors`）体积过大（约 **1.7 GB**），远超 Git 的合理使用范围，因此已在 `.gitignore` 中排除。

## 使用方式

训练脚本会自动从 Hugging Face 下载模型权重。如需手动下载：

```bash
huggingface-cli download Qwen/Qwen3.5-0.8B --local-dir qwen/Qwen3.5-0.8B
```

## 跟踪的文件

本目录下的配置/分词器文件（`config.json`, `tokenizer_config.json` 等）仍被 Git 跟踪。权重文件需自行下载或由脚本自动拉取。