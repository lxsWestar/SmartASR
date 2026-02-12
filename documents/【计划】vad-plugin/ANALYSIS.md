# VAD 插件化 - 方案分析

> 创建日期: 2026-02-04

## 1. 背景

### 问题描述

当前 `ali_qwen.py` (云端 API) 调用 `vad_utils.py` 时，如果 `silero` 不可用会回退到 `funasr`，导致：

```
funasr version: 1.3.1.
Downloading Model from https://www.modelscope.cn to directory: ...
```

**云端 API 不应该下载本地模型！**

### 现有代码

```
stt/
├── vad_utils.py      # 526 行，3 种 VAD 方法混在一起
├── engines/
│   ├── ali_qwen.py   # 云端 API，不想下载模型
│   └── ali_funasr.py # 本地引擎，可以用 funasr VAD
```

### 参考项目做法

`pyvideotrans` 的 `_base.py` 使用 `faster_whisper.vad` 的 silero：

```python
def cut_audio(self):
    from faster_whisper.vad import VadOptions, get_speech_timestamps
    # silero-vad 内置，无需下载
```

---

## 2. 方案对比

### 方案 A: VAD 插件化 (推荐)

```
stt/vad/
├── manager.py     # 中控
├── plugins/
│   ├── silero.py  # requires_download = False
│   └── funasr.py  # requires_download = True
```

**优点:**
- 架构清晰，与 STT 引擎一致
- 可按需排除方法: `exclude=["funasr"]`
- 扩展性好，添加新 VAD 只需放文件

**缺点:**
- 需要重构，工作量较大

### 方案 B: 保持现状，硬编码

直接在 `ali_qwen.py` 中写死只用 silero/pydub：

```python
def _cut_audio_with_vad(self):
    # 只用 silero，不用 vad_utils
    from faster_whisper.vad import ...
```

**优点:**
- 改动最小，立即见效

**缺点:**
- 重复代码
- 不够灵活

### 方案 C: vad_utils 添加参数

```python
def cut_audio_by_vad(audio_path, exclude_methods=["funasr"]):
    ...
```

**优点:**
- 改动较小

**缺点:**
- 不是根本解决，代码仍然耦合

---

## 3. 技术验证

### STT 引擎插件架构 (已验证)

```python
# registry.py
@register_engine
class MyEngine(BaseSTTEngine):
    name = "my_engine"

# engines/__init__.py
def _auto_discover():
    for file in engines_dir.glob("*.py"):
        if not file.name.startswith("_"):
            importlib.import_module(...)
```

**可直接复用此模式用于 VAD。**

### vad_utils.py 代码分析

| 组件 | 行数 | 可迁移性 |
|------|------|----------|
| VADConfig | ~20 | ✅ 直接迁移到 vad/dto.py |
| VADSegment | ~10 | ✅ 直接迁移到 vad/dto.py |
| _check_silero_available | ~10 | ✅ 迁移到 plugins/silero.py |
| _check_funasr_available | ~10 | ✅ 迁移到 plugins/funasr.py |
| _detect_with_silero | ~50 | ✅ 迁移到 plugins/silero.py |
| _detect_with_funasr | ~80 | ✅ 迁移到 plugins/funasr.py |
| _detect_with_pydub | ~50 | ✅ 迁移到 plugins/pydub.py |
| cut_audio_by_vad | ~100 | ✅ 迁移到 manager.py |

**结论: 代码可平滑迁移，无需重写。**

---

## 4. 核心接口设计

### BaseVAD 基类

```python
@dataclass
class BaseVAD:
    name: str                    # 插件标识
    display_name: str            # 显示名称
    requires_download: bool      # 是否需要下载模型
    
    def check_available(self) -> Tuple[bool, str]:
        """检查依赖是否安装"""
        ...
    
    def detect(self, audio_path: Path, config: VADConfig) -> List[VADSegment]:
        """检测语音片段"""
        ...
    
    def cut_audio(self, audio_path: Path, output_dir: Path, config: VADConfig) -> List[AudioChunk]:
        """切分音频文件"""
        ...
```

### VADManager 中控

```python
class VADManager:
    def cut_audio(
        self,
        audio_path: Path,
        output_dir: Path,
        method: str = "auto",
        exclude: List[str] = None,       # 排除方法
        require_no_download: bool = False, # 只用无需下载的
        config: VADConfig = None,
    ) -> List[AudioChunk]:
        ...
```

### 使用示例

```python
# 云端 API (不下载模型)
manager = VADManager()
chunks = manager.cut_audio(audio, output, require_no_download=True)

# 本地引擎 (可用任何方法)
chunks = manager.cut_audio(audio, output, method="funasr")
```

---

## 5. 风险评估

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|----------|
| 循环导入 | 低 | 中 | VAD 单向依赖，不引用 STT |
| 迁移遗漏 | 中 | 低 | 保留 vad_utils.py 一段时间 |
| 接口不兼容 | 低 | 中 | 先写测试再重构 |

---

## 6. 决策

**采用方案 A (VAD 插件化)**，理由：

1. 与 STT 引擎架构一致
2. 现有代码可平滑迁移
3. 解决云端 API 下载模型的问题
4. 长期可维护性好

**执行策略:**

1. **临时方案**: 先修改 `ali_qwen.py` 硬编码 silero，验证 API 可用
2. **正式重构**: 按 Phase 1-5 逐步实施 VAD 插件化
