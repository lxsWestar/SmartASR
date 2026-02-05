# VAD 插件化 - 任务清单

> 状态: 📋 计划中

## 目标

将 VAD 重构为插件架构，实现：
- 放文件即注册，删文件即移除
- 云端 API 可排除需下载模型的 VAD
- 与 STT 引擎共享模型源配置

## 目录结构

```
backend/app/services/stt/
├── vad/                      # VAD 子模块
│   ├── __init__.py           # 导出 VADManager
│   ├── base.py               # BaseVAD 基类
│   ├── registry.py           # @register_vad 装饰器
│   ├── manager.py            # VAD 中控管理器
│   ├── dto.py                # VADConfig, VADSegment
│   ├── README.md             # 插件开发文档
│   └── plugins/              # VAD 插件目录
│       ├── __init__.py       # 自动发现
│       ├── _template.py      # 插件模板
│       ├── silero.py         # silero-vad (推荐)
│       ├── funasr.py         # FunASR fsmn-vad
│       ├── pydub.py          # pydub 静音检测
│       └── duration.py       # 按时长切分
└── vad_utils.py              # [废弃] 迁移后删除
```

---

## Phase 1: 基础架构

- [ ] 1.1 创建 `vad/` 目录结构
- [ ] 1.2 实现 `vad/dto.py`
  - VADConfig (配置参数)
  - VADSegment (检测结果)
  - AudioChunk (切分片段)
- [ ] 1.3 实现 `vad/base.py`
  - BaseVAD 基类
  - 抽象方法: check_available(), detect(), cut_audio()
- [ ] 1.4 实现 `vad/registry.py`
  - @register_vad 装饰器
  - list_vad_plugins(), get_vad_plugin()
- [ ] 1.5 实现 `vad/plugins/__init__.py`
  - 自动发现机制

## Phase 2: VAD 插件实现

- [ ] 2.1 `plugins/silero.py`
  - 基于 faster_whisper 内置 silero-vad
  - requires_download = False
  - 推荐用于云端 API
- [ ] 2.2 `plugins/funasr.py`
  - 基于 FunASR fsmn-vad
  - requires_download = True
  - 支持 ModelSourceConfig
- [ ] 2.3 `plugins/pydub.py`
  - 基于 pydub 静音检测
  - requires_download = False
  - 轻量级替代方案
- [ ] 2.4 `plugins/duration.py`
  - 按固定时长切分
  - requires_download = False
  - 最终回退方案
- [ ] 2.5 `plugins/_template.py`
  - 插件开发模板

## Phase 3: VAD 中控管理器

- [ ] 3.1 实现 `vad/manager.py`
- [ ] 3.2 支持方法自动选择 (method="auto")
- [ ] 3.3 支持排除指定方法 (exclude=["funasr"])
- [ ] 3.4 支持 requires_download 过滤
- [ ] 3.5 支持模型源配置 (与 STT 共享 ModelSourceConfig)

## Phase 4: 集成重构

- [ ] 4.1 重构 `ali_qwen.py` 使用 VADManager
- [ ] 4.2 重构 `ali_funasr.py` 使用 VADManager
- [ ] 4.3 迁移 `vad_utils.py` 内容
- [ ] 4.4 删除旧的 `vad_utils.py`
- [ ] 4.5 更新 `__init__.py` 导出

## Phase 5: 文档和测试

- [ ] 5.1 编写 `vad/README.md` 插件开发文档
- [ ] 5.2 单元测试: 各 VAD 插件
- [ ] 5.3 集成测试: VADManager
- [ ] 5.4 端到端测试: STT 引擎 + VAD

---

## 依赖关系

```
Phase 1 ──► Phase 2 ──► Phase 3 ──► Phase 4 ──► Phase 5
  │           │           │           │
  └───────────┴───────────┴───────────┘
              可并行开发插件
```

## 预计工时

| Phase | 预计时间 |
|-------|----------|
| Phase 1 | 1-2 小时 |
| Phase 2 | 2-3 小时 |
| Phase 3 | 1-2 小时 |
| Phase 4 | 1-2 小时 |
| Phase 5 | 1-2 小时 |
| **总计** | **6-11 小时** |
