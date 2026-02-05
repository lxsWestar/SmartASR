# 模型目录

此目录用于存放 FunASR 模型文件。

## 模型加载优先级

```
1. ./models/          ← 本目录 (推荐)
2. 内网服务器          ← STT_MODEL_SERVER 环境变量
3. 官方源自动下载      ← ModelScope / HuggingFace
```

## 支持的模型

| 目录名 | 说明 | 大小 |
|--------|------|------|
| `SenseVoiceSmall/` | 多语言 (zh/en/ja/ko/yue) | ~900MB |
| `paraformer-zh/` | 中文专用 | ~1GB |
| `fsmn-vad/` | VAD 语音检测 (可选) | ~10MB |
| `ct-punc/` | 标点恢复 (可选) | ~300MB |

## 手动下载

### 方式 1: 使用 modelscope-cli

```bash
pip install modelscope
modelscope download --model iic/SenseVoiceSmall --local_dir ./SenseVoiceSmall
```

### 方式 2: 从内网服务器复制

```bash
# 如果公司有模型服务器
scp -r user@192.168.1.100:/models/SenseVoiceSmall ./
```

### 方式 3: 手动下载

1. 访问 https://modelscope.cn/models/iic/SenseVoiceSmall
2. 下载所有文件
3. 解压到 `models/SenseVoiceSmall/`

## 目录结构示例

```
models/
├── .gitkeep
├── README.md
├── SenseVoiceSmall/
│   ├── config.yaml
│   ├── model.pt
│   ├── tokens.json
│   └── ...
├── paraformer-zh/
│   └── ...
└── fsmn-vad/
    └── ...
```
