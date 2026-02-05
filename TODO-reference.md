# SmartASR: 源码参考 (pyvideotrans)

> 📚 本文件记录从 pyvideotrans 提取的关键信息，仅作开发参考。
> ⚠️ **注意**: pyvideotrans/ 目录为只读，不要修改其中的任何内容。

---

## 1. 参考项目目录结构

```
pyvideotrans/videotrans/
├── recognition/              # 语音识别模块 ← 主要参考
│   ├── __init__.py          # 常量 + if-elif 分发 (我们改用装饰器)
│   ├── _base.py             # 基类 BaseRecogn (@dataclass)
│   ├── _funasr.py           # FunASR 实现 ← 参考
│   ├── _qwen3asr.py         # Qwen-ASR 实现 ← 参考
│   └── _*.py                # 其他 17 个引擎...
├── configure/
│   ├── config.py            # 全局配置
│   └── _except.py           # 异常类定义 ← 参考
└── util/
    └── help_ffmpeg.py       # FFmpeg 工具 ← 参考
```

---

## 2. 与参考项目对比

| 参考项目 (pyvideotrans) | 本项目 (SmartASR) | 改进点 |
|------------------------|-------------------|--------|
| `recognition/__init__.py` 用 if-elif 分发 | `registry.py` 用装饰器自动注册 | 放文件即用，无需改代码 |
| `_base.py` 用 @dataclass | `base.py` 保持 dataclass 风格 | 更简洁 |
| 引擎文件用 `_` 前缀 | 引擎无前缀，`_template.py` 除外 | 更直观 |
| 配置分散多文件 | `config.py` 单文件 | 便于嵌入 |
| 无独立 DTO | 新增 `dto.py` | API 自描述更清晰 |

---

## 3. 音频预处理

**源文件**: `pyvideotrans/videotrans/util/help_ffmpeg.py`

### 关键点
- FFmpeg 参数: `["-y", "-i", input, "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", output]`
- Windows 路径需用 `.as_posix()` 处理

### 参考代码
```python
# 音频转换为 16kHz mono WAV
cmd = [
    "ffmpeg",
    "-y",              # 覆盖输出文件
    "-i", input_path,  # 输入文件
    "-ac", "1",        # 单声道
    "-ar", "16000",    # 16kHz 采样率
    "-c:a", "pcm_s16le",  # PCM 编码
    output_path
]
```

---

## 4. 引擎基类设计

**源文件**: `pyvideotrans/videotrans/recognition/_base.py`

### 关键点
- 使用 `@dataclass` 装饰器
- `__post_init__` 中初始化设备检测
- `run()` 方法调用 `_exec()` 抽象方法

### 参考代码
```python
from dataclasses import dataclass, field

@dataclass
class BaseRecogn:
    """语音识别基类"""
    
    # 配置参数
    language: str = "zh"
    model: str = ""
    
    # 运行时状态
    device: str = field(default="cpu", init=False)
    is_cuda: bool = field(default=False, init=False)
    
    def __post_init__(self):
        """初始化后检测 CUDA"""
        try:
            import torch
            self.is_cuda = torch.cuda.is_available()
            self.device = "cuda" if self.is_cuda else "cpu"
        except ImportError:
            pass
    
    def run(self):
        """主入口"""
        return self._exec()
    
    def _exec(self):
        """子类实现"""
        raise NotImplementedError
```

---

## 5. FunASR 实现参考

**源文件**: `pyvideotrans/videotrans/recognition/_funasr.py`

### 关键点
- 支持 SenseVoiceSmall 和 paraformer 两种模型
- 模型目录: `config.ROOT_DIR + "/models"`
- 使用 `funasr.AutoModel` 加载

### 参考代码
```python
from funasr import AutoModel

class FunASRRecogn(BaseRecogn):
    def _exec(self):
        # 加载模型
        model = AutoModel(
            model="iic/SenseVoiceSmall",
            vad_model="iic/fsmn-vad",
            punc_model="iic/ct-punc",
            device=self.device,
        )
        
        # 执行识别
        result = model.generate(
            input=str(self.audio_path),
            batch_size_s=300,
            hotword=""
        )
        
        return result
```

---

## 6. Qwen-ASR 实现参考

**源文件**: `pyvideotrans/videotrans/recognition/_qwen3asr.py`

### 关键点
- 使用 `dashscope.MultiModalConversation.call()`
- API Key 从 `config.params.get('qwenmt_key')` 获取
- 支持 `asr_options` 参数

### 参考代码
```python
from dashscope import MultiModalConversation

class QwenASRRecogn(BaseRecogn):
    def _exec(self):
        # 获取 API Key
        api_key = config.params.get('qwenmt_key')
        
        # 调用 API
        response = MultiModalConversation.call(
            model="qwen-audio-asr",
            messages=[{
                "role": "user",
                "content": [
                    {"audio": self.audio_url},
                    {"text": "请将这段音频转为文字"}
                ]
            }],
            api_key=api_key
        )
        
        return response.output.text
```

---

## 7. 环境设置

### 必须设置
```python
import os

# 防止 OpenMP 线程冲突
os.environ["OMP_NUM_THREADS"] = "1"

# 允许 KMP 库重复加载
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
```

---

## 8. 其他引擎参考

### 引擎列表
| 文件 | 引擎 | 类型 | 说明 |
|------|------|------|------|
| `_deepgram.py` | Deepgram | 云端 | 企业级 API |
| `_google.py` | Google Cloud STT | 云端 | 多语言支持 |
| `_whisper.py` | Whisper | 本地 | OpenAI 模型 |
| `_elevenlabs.py` | ElevenLabs | 云端 | 语音合成公司的 STT |
| `_gemini.py` | Google Gemini | 云端 | 大模型 |
| `_huggingface.py` | HuggingFace | 云端 | 模型库 API |
| `_openairecognapi.py` | OpenAI Whisper API | 云端 | 官方 API |
| `_doubao.py` | 字节豆包 | 云端 | 字节跳动 |
| `_ai302.py` | AI302 | 云端 | 聚合 API |

### 通用模式
大部分云端引擎的实现模式:
1. 检查 API Key
2. 使用 VAD 切分长音频
3. 逐段调用 API
4. 汇总结果

---

## 9. VAD 实现参考

### 使用 silero-vad (faster_whisper)
```python
from faster_whisper import vad

def cut_audio(audio_path):
    """使用 silero-vad 切分音频"""
    segments = vad.get_speech_timestamps(audio_path)
    return segments
```

### 使用 pydub
```python
from pydub import AudioSegment
from pydub.silence import detect_nonsilent

def detect_speech(audio_path):
    """使用 pydub 检测语音"""
    audio = AudioSegment.from_file(audio_path)
    segments = detect_nonsilent(
        audio,
        min_silence_len=500,
        silence_thresh=-40
    )
    return segments
```

---

## 10. 错误处理参考

**源文件**: `pyvideotrans/videotrans/configure/_except.py`

### 异常类结构
```python
class BaseException(Exception):
    """基础异常类"""
    pass

class MediaException(BaseException):
    """媒体处理异常"""
    pass

class RecognizeException(BaseException):
    """识别异常"""
    pass
```
