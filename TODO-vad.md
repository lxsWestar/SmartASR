# TODO: VAD 插件化重构

> VAD 作为 STT 的子模块，由 STT 统一管理

## 目录结构设计

```
backend/app/services/stt/
├── vad/                      # VAD 子模块
│   ├── __init__.py           # 导出 VADManager 和主要接口
│   ├── base.py               # BaseVAD 基类
│   ├── registry.py           # VAD 注册表 (@register_vad)
│   ├── manager.py            # VAD 中控管理器
│   ├── dto.py                # VADConfig, VADSegment
│   ├── README.md             # 插件开发文档
│   └── plugins/              # VAD 插件目录 (放文件即注册)
│       ├── __init__.py       # 自动发现和加载
│       ├── _template.py      # 插件模板
│       ├── silero.py         # silero-vad (faster_whisper)
│       ├── funasr.py         # FunASR fsmn-vad
│       ├── pydub.py          # pydub 静音检测
│       └── duration.py       # 按时长切分 (回退)
├── engines/                  # STT 引擎 (使用 VAD 子模块)
│   ├── ali_qwen.py           # 云端引擎 -> 使用 vad.VADManager
│   └── ali_funasr.py         # 本地引擎 -> 使用 vad.VADManager
└── vad_utils.py              # [废弃] 迁移到 vad/ 后删除
```

## 任务清单

### Phase 1: 基础架构
- [ ] 1.1 创建 `vad/` 目录结构
- [ ] 1.2 实现 `vad/dto.py` (VADConfig, VADSegment)
- [ ] 1.3 实现 `vad/base.py` (BaseVAD 基类)
- [ ] 1.4 实现 `vad/registry.py` (@register_vad 装饰器)
- [ ] 1.5 实现 `vad/plugins/__init__.py` (自动发现)

### Phase 2: VAD 插件实现
- [ ] 2.1 实现 `plugins/silero.py` (推荐，无需下载)
- [ ] 2.2 实现 `plugins/funasr.py` (需下载模型)
- [ ] 2.3 实现 `plugins/pydub.py` (轻量级)
- [ ] 2.4 实现 `plugins/duration.py` (回退方案)
- [ ] 2.5 创建 `plugins/_template.py` (开发模板)

### Phase 3: 中控管理器
- [ ] 3.1 实现 `vad/manager.py` (VADManager)
- [ ] 3.2 支持方法自动选择 (auto)
- [ ] 3.3 支持排除指定方法 (exclude=["funasr"])
- [ ] 3.4 支持模型源配置 (与 STT 共享)

### Phase 4: 集成重构
- [ ] 4.1 重构 `ali_qwen.py` 使用 VADManager
- [ ] 4.2 重构 `ali_funasr.py` 使用 VADManager
- [ ] 4.3 迁移 `vad_utils.py` 内容到 vad/
- [ ] 4.4 删除旧的 `vad_utils.py`

### Phase 5: 文档和测试
- [ ] 5.1 编写 `vad/README.md` 插件开发文档
- [ ] 5.2 测试阿里云端 API (日语音频)
- [ ] 5.3 测试本地 FunASR (日语音频)
- [ ] 5.4 添加单元测试

---

## 核心接口设计

### BaseVAD 基类
```python
@dataclass
class BaseVAD:
    name: str                    # 插件标识
    display_name: str            # 显示名称
    requires_download: bool      # 是否需要下载模型
    
    def check_available(self) -> Tuple[bool, str]: ...
    def detect(self, audio_path: Path, config: VADConfig) -> List[VADSegment]: ...
    def cut_audio(self, audio_path: Path, output_dir: Path, config: VADConfig) -> List[AudioChunk]: ...
```

### VADManager 中控
```python
class VADManager:
    def detect(
        self,
        audio_path: Path,
        method: str = "auto",           # 指定方法或自动
        exclude: List[str] = None,      # 排除方法 (如云端不用 funasr)
        config: VADConfig = None,
    ) -> List[VADSegment]: ...
    
    def cut_audio(
        self,
        audio_path: Path,
        output_dir: Path,
        method: str = "auto",
        exclude: List[str] = None,
        config: VADConfig = None,
    ) -> List[AudioChunk]: ...
    
    def list_plugins(self) -> List[str]: ...
    def get_available_plugins(self, exclude_download: bool = False) -> List[str]: ...
```

### 使用示例
```python
from backend.app.services.stt.vad import VADManager, VADConfig

# STT 引擎中使用
manager = VADManager()

# 云端 API: 不使用需要下载模型的 VAD
chunks = manager.cut_audio(
    audio_path,
    output_dir,
    exclude=["funasr"],  # 排除 funasr
)

# 本地引擎: 可以使用任何 VAD
chunks = manager.cut_audio(
    audio_path,
    output_dir,
    method="funasr",  # 明确指定
)
```

---

## 需要的 API Keys

| 服务 | 环境变量 | 用途 |
|------|----------|------|
| 阿里百炼 | `DASHSCOPE_API_KEY` | Qwen ASR 云端 API |

当前已有: `sk-df8287f9b5004b42947408ef09e28b17`

---

## 测试音频

- 日语 NHK: `D:\tmp\fc5270a9e2d0964b40ec0ffec65f2ba6_64k.mp3`
