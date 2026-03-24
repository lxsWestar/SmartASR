# SmartASR 开发与运营指南

> 由 document-project 工作流生成 | 扫描级别: exhaustive | 日期: 2026-03-02

---

## 快速开始

### 开发环境搭建

```bash
# 1. 克隆仓库
git clone https://github.com/yourusername/SmartASR
cd SmartASR

# 2. 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# 3. 安装完整开发依赖
pip install -e ".[all]"

# 4. 复制配置文件
cp config.example.json config.json
# 编辑 config.json 修改 models_dir、cache_dir 等

# 5. 验证安装
smartasr --version
```

### 安装 FFmpeg（必须）

| 平台 | 命令 |
|------|------|
| Windows | `winget install ffmpeg` 或 `choco install ffmpeg` |
| macOS | `brew install ffmpeg` |
| Ubuntu/Debian | `sudo apt install ffmpeg` |

---

## 运行方式

### 方式一：启动 API 服务

```bash
# 使用 CLI（推荐）
smartasr serve --host 0.0.0.0 --port 8000

# 直接运行
python run.py

# uvicorn 直接启动
uvicorn backend.app.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 方式二：命令行识别

```bash
# 基础使用
smartasr transcribe audio.mp3

# 指定引擎和输出格式
smartasr transcribe audio.mp3 --engine ali_funasr --output result.srt

# 指定模型
smartasr transcribe audio.mp3 --model SenseVoiceSmall

# 指定语言
smartasr transcribe audio.mp3 --language ja
```

### 方式三：直接调用 API

```bash
# 同步识别
curl -X POST http://localhost:8000/api/stt/transcribe \
  -F "file=@audio.mp3" \
  -F "engine=ali_funasr" \
  -F "language=zh"

# 异步识别
curl -X POST http://localhost:8000/api/stt/transcribe/async \
  -F "file=@audio.mp3" \
  -F "engine=ali_funasr"
```

---

## 模型下载

### FunASR 模型（自动下载）

首次运行时 FunASR 自动从 ModelScope 下载模型（需要网络）：

| 模型 | 大小 | 说明 |
|------|------|------|
| SenseVoiceSmall | ~900MB | 默认多语言模型 |
| paraformer-zh | ~1.2GB | 中文专用 |
| fsmn-vad | ~100MB | VAD 模型（SenseVoice 必需） |
| ct-punc | ~80MB | 标点恢复（paraformer 必需） |
| cam++ | ~200MB | 说话人分离（可选） |

### 手动下载（网络受限环境）

```bash
# 下载 SenseVoiceSmall
python scripts/download_sensevoice_small_files.py
```

### 内网模型服务器

```bash
# 在有网络的机器上启动模型服务器
python scripts/model_server.py --models-dir D:\models\funasr --port 8765

# 其他机器配置
export STT_MODEL_SERVER=http://192.168.1.100:8765
```

---

## 配置管理

### 配置文件（config.json）

加载顺序（按优先级）：
1. `STT_CONFIG_FILE` 环境变量指定的文件
2. 当前目录 `config.json`
3. 项目根目录 `config.json`
4. 从环境变量构建默认配置

### 关键配置项

```json
{
  "models_dir": "D:/models/SmartASR",     // 模型目录
  "cache_dir": "D:/cache/SmartASR",        // 临时文件目录
  "max_file_size_mb": 500,                 // 最大上传文件大小
  "default_engine": "ali_funasr",          // 默认引擎
  "api_timeout": 300,                      // API 超时（秒）
  "model_source": {
    "source_type": "auto",                 // local/network/official/auto
    "local_dir": "D:/models/funasr",       // 本地模型目录
    "network_server": "http://...",        // 内网服务器
    "official_hub": "ms"                   // hf=HuggingFace, ms=ModelScope
  }
}
```

### 环境变量参考

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `STT_CONFIG_FILE` | 配置文件路径 | 无 |
| `STT_MODELS_DIR` | 模型存储目录 | 系统缓存目录 |
| `STT_CACHE_DIR` | 临时文件目录 | 系统缓存目录 |
| `STT_MAX_FILE_SIZE_MB` | 最大文件大小（MB） | 500 |
| `STT_DEFAULT_ENGINE` | 默认引擎 | ali_funasr |
| `STT_API_TIMEOUT` | API 超时（秒） | 300 |
| `STT_MODEL_SOURCE` | 模型来源类型 | auto |
| `STT_MODEL_SERVER` | 内网模型服务器 URL | 无 |
| `FUNASR_HUB` | 官方 hub 选择（hf/ms） | ms |
| `DASHSCOPE_API_KEY` | 通义千问 API Key | 无 |

---

## 开发工作流

### 测试

```bash
# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit/

# 运行带覆盖率报告
pytest --cov=backend --cov-report=html

# 快速冒烟测试
python tests/quick_test.py
```

### 代码格式化

```bash
# 格式化代码
black backend/ tests/

# 排序 import
isort backend/ tests/

# 类型检查
mypy backend/
```

### 添加新引擎

1. 复制模板文件：`cp backend/app/services/stt/engines/_template.py backend/app/services/stt/engines/my_engine.py`
2. 实现 `BaseSTTEngine` 的 4 个抽象方法：
   - `get_metadata()` — 返回引擎描述
   - `transcribe()` — 执行识别
   - `get_models()` — 返回模型列表
   - `check_available()` — 检查可用性
3. 在类上添加 `@register_engine` 装饰器
4. 文件即注册，无需修改其他代码

```python
from backend.app.services.stt.base import BaseSTTEngine
from backend.app.services.stt.registry import register_engine

@register_engine
@dataclass
class MyEngine(BaseSTTEngine):
    name: str = field(default="my_engine", init=False)
    display_name: str = field(default="My Engine", init=False)
    engine_type: str = field(default="local", init=False)
    ...
```

---

## 项目状态

### 当前版本

| 属性 | 值 |
|------|---|
| 版本号 | 0.1.0 |
| 开发阶段 | Alpha |
| Python 支持 | 3.10 / 3.11 / 3.12 |
| 许可证 | MIT |

### 已实现功能 ✅

- FastAPI REST API 服务
- 同步 + 异步识别
- 任务管理（提交/查询/取消/删除）
- FunASR 本地引擎（SenseVoiceSmall + paraformer-zh）
- 通义千问云端引擎（qwen3-asr-flash/turbo）
- 多后端 VAD 系统（silero/funasr/pydub 降级）
- 三级模型来源策略（本地/内网/官方）
- CLI 工具（transcribe/serve/engines/config）
- 多格式输出（TXT/JSON/SRT/VTT/TSV）
- 静态前端 Web UI
- Webhook 回调
- 进度追踪

### 计划中功能 🔲

- VAD 插件化（见 `documents/【计划】vad-plugin/`）
- Docker 容器化部署
- 持久化任务存储（Redis/SQLite）
- WebSocket 实时进度推送
- 更多语音识别引擎支持

---

## 已知限制

| 限制 | 说明 |
|------|------|
| 任务存储 | 仅内存存储，重启后丢失 |
| 并发 | 无并发控制，多请求同时运行可能引发内存问题 |
| CORS | 当前允许所有来源，生产环境需限制 |
| 认证 | 无认证机制，勿暴露到公网 |
| HTML 路径（Windows） | FFmpeg 命令行路径需特殊处理（`compat.to_ffmpeg_path()`） |

---

## 目录规范

- `backend/app/services/stt/engines/` — 所有引擎插件的存放位置
- `backend/app/api/routers/` — 所有 API 路由
- `backend/app/cli/commands/` — 所有 CLI 子命令
- `backend/app/cli/formatters/` — 所有输出格式化器
- `tests/unit/` — 不依赖外部服务的单元测试
- `tests/integration/` — 依赖 API 服务的集成测试
- `tests/e2e/` — 端到端流程测试
- `docs/` — AI 协作上下文文档（由 BMAD 生成）
- `documents/` — 人工编写的设计文档和指南
