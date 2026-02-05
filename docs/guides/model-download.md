# FunASR 模型依赖关系说明

## 核心概念

FunASR 有 **2 种识别路径**，每种路径需要不同的模型组合：

---

## 路径 1: Paraformer（中文专用）

```
用途: 中文识别，支持说话人分离
流程: 一次性处理整个音频，内置 VAD

必需模型:
├── paraformer-zh (主模型，~1.2GB)
├── fsmn-vad (VAD 模型，~5MB)
└── ct-punc (标点模型，~50MB)

可选模型:
└── cam++ (说话人分离，~100MB，仅在 max_speakers>-1 时需要)
```

**下载地址：**
- HuggingFace: https://huggingface.co/funasr/paraformer-zh
- ModelScope: https://modelscope.cn/models/iic/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch

---

## 路径 2: SenseVoice（多语言）

```
用途: 中英日韩粤语识别
流程: VAD 切分 → 逐段识别

必需模型:
├── SenseVoiceSmall (主模型，~900MB)
├── fsmn-vad (VAD 模型，~5MB)
└── ct-punc (标点模型，~50MB)
```

**下载地址：**
- ⚠️ **仅 ModelScope 有**: https://modelscope.cn/models/iic/SenseVoiceSmall
- HuggingFace **没有** SenseVoice（这就是为什么海外下载慢）

---

## 公共依赖模型

这两个模型是 **共用的**，只需下载一次：

| 模型 | 作用 | 大小 | HuggingFace | ModelScope |
|------|------|------|-------------|------------|
| **fsmn-vad** | 语音活动检测（切分静音） | ~5MB | ✅ funasr/fsmn-vad | ✅ iic/speech_fsmn_vad_zh-cn-16k-common-pytorch |
| **ct-punc** | 标点符号预测 | ~50MB | ✅ funasr/ct-punc | ✅ iic/punc_ct-transformer_zh-cn-common-vocab272727-pytorch |

---

## 你在东京应该下载什么？

### 选项 A：只用 Paraformer（推荐，HuggingFace 快）✅

```powershell
# 这 3 个在 HuggingFace 上都有
cd D:\models
git clone https://huggingface.co/funasr/paraformer-zh
git clone https://huggingface.co/funasr/fsmn-vad
git clone https://huggingface.co/funasr/ct-punc
```

**优点**：
- HuggingFace 海外快
- 仅 ~1.3GB
- 中文识别足够用

**缺点**：
- 不支持日语（但你测试音频是日语）

---

### 选项 B：用 SenseVoice（支持日语，但要从 ModelScope 下载）

```powershell
# SenseVoice 只在 ModelScope，可能需要断点续传工具
# 方法 1: git clone（支持断点）
cd D:\models
git clone https://www.modelscope.cn/iic/SenseVoiceSmall.git

# 方法 2: modelscope 命令行工具
pip install modelscope
python -c "from modelscope import snapshot_download; snapshot_download('iic/SenseVoiceSmall', cache_dir='D:/models')"

# 公共依赖（HuggingFace 或 ModelScope 任选）
git clone https://huggingface.co/funasr/fsmn-vad
git clone https://huggingface.co/funasr/ct-punc
```

**优点**：
- 支持日语、韩语等多语言
- 你的 NHK 测试音频需要这个

**缺点**：
- ModelScope 从日本下载慢
- ~900MB

---

## 我的建议

**立即行动**：
1. 先下载 **Paraformer + 公共依赖**（从 HuggingFace，快）
2. 测试中文识别能否跑通
3. 如果需要日语，再单独下载 SenseVoice（用断点续传工具）

**目录结构**：
```
D:\models\funasr\
├── paraformer-zh\
│   ├── config.yaml
│   ├── model.pt
│   └── ...
├── fsmn-vad\
│   └── ...
└── ct-punc\
    └── ...
```

要我帮你生成下载脚本吗？
