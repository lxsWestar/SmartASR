# AGENTS.md - AI 协作全局规范

> 本文件定义 AI Agent 与人类开发者协作的全局规则。

## 项目概述

**SmartASR** 是一个轻量级语音转文字 (STT) API 服务，从 `pyvideotrans` 提取核心逻辑构建。

### 核心原则
- **单一职责**: 只做语音识别，不做字幕/视频处理
- **插件架构**: 引擎可热插拔，放文件即注册
- **跨平台**: Windows/Linux/macOS 通用

### 📄 许可证
- **SmartASR 核心代码**: MIT License（可商用）
- **pyvideotrans/ 参考代码**: GPL v3（仅作参考，运行时不依赖）
- **合规审查**: 见 [COMPLIANCE.md](COMPLIANCE.md)

---

## AI Agent 行为规范

### 1. 代码修改规则

```yaml
禁止操作:
  - 修改 pyvideotrans/ 目录下任何文件 (只读参考)
  - 删除已有的异常处理代码
  - 移除类型注解
  - 使用 print() 替代 logging

必须遵守:
  - 所有公共函数必须有 documentstring
  - 异常必须使用 backend/app/services/stt/exceptions.py 中定义的类
  - 路径处理必须使用 pathlib.Path
  - Windows 路径传递给 FFmpeg 时用 .as_posix()
```

### 2. 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 类名 | PascalCase | `BaseSTTEngine`, `FunASREngine` |
| 函数/方法 | snake_case | `check_ffmpeg()`, `get_models()` |
| 常量 | UPPER_SNAKE_CASE | `IS_WINDOWS`, `DEFAULT_SAMPLE_RATE` |
| 私有成员 | 前缀 `_` | `_model`, `_engine_registry` |
| 引擎文件 | 小写 + 下划线 | `ali_funasr.py`, `ali_qwen.py` |

### 3. 文件创建规则

```yaml
新建引擎:
  位置: backend/app/services/stt/engines/
  模板: 复制 _template.py 并重命名
  必须: 使用 @register_engine 装饰器

新建测试:
  位置: tests/{unit|integration|e2e}/test_{模块名}/
  命名: test_{功能}.py
  必须: 使用 pytest fixtures

新建文档:
  位置: documents/{api|design|guides}/
  格式: Markdown
```

### 4. 依赖管理

```yaml
核心依赖 (必需):
  - pathlib (标准库)
  - dataclasses (标准库)
  - typing (标准库)

可选依赖 (按需安装):
  - funasr: ali_funasr 引擎
  - dashscope: ali_qwen 引擎
  - torch: GPU 加速
  - fastapi: API 服务
  - faster-whisper: silero-vad (推荐 VAD)
  - pydub: 轻量级 VAD / 音频切分

禁止添加:
  - 大型框架 (Django, Flask 等) 到核心模块
  - 与 STT 无关的库
```

---

## 变量名索引

> 全局变量名统一管理，避免命名冲突

### 配置相关
| 变量名 | 类型 | 位置 | 说明 |
|--------|------|------|------|
| `IS_WINDOWS` | bool | compat.py | 是否 Windows 系统 |
| `IS_LINUX` | bool | compat.py | 是否 Linux 系统 |
| `IS_MACOS` | bool | compat.py | 是否 macOS 系统 |
| `STTConfig` | dataclass | config.py | 配置类，含 default_sample_rate=16000 |

### 注册表相关
| 变量名 | 类型 | 位置 | 说明 |
|--------|------|------|------|
| `_engine_registry` | Dict | registry.py | 引擎类注册表 |
| `_engine_instances` | Dict | registry.py | 引擎实例缓存 |

### VAD 相关
| 变量名/类型 | 类型 | 位置 | 说明 |
|------------|------|------|------|
| `VADMethod` | Literal | vad_utils.py | VAD 方法类型: "auto", "silero", "funasr", "pydub" |
| `VADConfig` | dataclass | vad_utils.py | VAD 配置参数 |
| `VADSegment` | dataclass | vad_utils.py | 检测到的语音片段 (start_ms, end_ms) |

### DTO 类名
| 类名 | 位置 | 说明 |
|------|------|------|
| `STTRequest` | dto.py | 识别请求 |
| `STTResponse` | dto.py | 识别结果 (含 usage 字段) |
| `STTSegment` | dto.py | 时间戳片段 |
| `UsageInfo` | dto.py | 单次请求使用量统计 (待实现) |
| `EngineMetadata` | dto.py | 引擎元数据 |
| `ModelInfo` | dto.py | 模型信息 |
| `ParameterSpec` | dto.py | 参数规格 |

---

## 任务状态追踪

> 参考 [TODO.md](TODO.md) 获取详细进度

| 里程碑 | 状态 | 负责 |
|--------|------|------|
| M1 项目骨架 | ✅ 完成 | Human + AI |
| M2 音频预处理 | ✅ 完成 | AI |
| M3 DTO + 接口 | ✅ 完成 | AI |
| M4 引擎注册 | ✅ 完成 | AI |
| M5 FunASR | ✅ 完成 | AI |
| M6 Qwen-ASR | ✅ 完成 | AI |
| M7 API 路由 | ✅ 完成 (OpenAI 兼容) | AI |
| M8 测试文档 | ✅ 完成 (119 unit tests) | AI |

---

## 上下文加载优先级

当 AI 需要理解项目时，按以下顺序读取：

1. `AGENTS.md` (本文件) - 全局规范
2. `TODO.md` - 开发计划和进度
3. `backend/app/services/stt/README.md` - 核心模块说明
4. 具体文件夹下的 `README.md` - 局部上下文
5. 代码文件头注释 - 文件级说明

---

## 常见任务模板

### 添加新引擎
```
1. 复制 engines/_template.py → engines/{engine_name}.py
2. 修改类名和元数据
3. 实现 check_available(), get_models(), transcribe()
4. 运行测试验证注册成功
```

### 修复 Bug
```
1. 确认问题复现
2. 定位代码位置
3. 检查相关 README.md 了解设计意图
4. 修改代码，保持向后兼容
5. 添加测试用例
```

### 添加新功能
```
1. 更新 TODO.md 记录需求
2. 设计接口 (先写 DTO)
3. 实现功能
4. 编写测试
5. 更新文档
```
