# TODO: 模型加载三段式重构

> 创建日期: 2026-02-05
> 优先级: 高
> 状态: 待实现

## 背景

用户克隆项目后，需要清晰的配置指南和统一的模型管理策略。

## 现状分析

### 1. 当前 README 配置说明

| 内容 | 是否完善 | 备注 |
|------|---------|------|
| 安装命令 | ✅ 有 | `pip install -e .` |
| 环境变量说明 | ⚠️ 部分 | 只提了 STT_MODELS_DIR |
| 初次配置向导 | ❌ 缺失 | 没有 step-by-step |
| 模型下载说明 | ❌ 缺失 | 用户不知道模型从哪来 |

### 2. 当前模型目录配置

| 来源 | 默认值 | 问题 |
|------|--------|------|
| `get_models_dir()` | `%LOCALAPPDATA%/SmartASR/models` (Win) | 分散在用户目录，不直观 |
| `STT_MODELS_DIR` 环境变量 | 用户指定 | 需要手动配置 |
| `config.json` | 用户指定 | 需要手动创建 |

**期望**: 默认使用项目根目录下的 `models/` 文件夹

### 3. 模型服务器脚本位置问题

当前 `scripts/model_file_server.py` 放在本项目内，但这个脚本是**给其他机器用的**，不应该属于 SmartASR 本体。

| 文件 | 当前位置 | 建议 |
|------|---------|------|
| `model_file_server.py` | `scripts/` | 移到独立仓库或 `tools/` |
| `model_server.py` | `scripts/` | 同上 |
| `download_*.py` | `scripts/` | ✅ 保留，属于项目 |

---

## 任务清单

### Phase 1: 统一模型目录 (优先)

- [ ] **1.1** 修改 `get_models_dir()` 默认返回 `项目根目录/models/`
  - 检测项目根目录 (通过 `pyproject.toml` 或 `.git` 定位)
  - 如果不在项目内运行，降级到 `~/.smartasr/models/`

- [ ] **1.2** 创建 `models/.gitkeep` 占位文件
  - 确保 git 追踪空目录
  - 添加 `models/*` 到 `.gitignore` (忽略模型文件)

- [ ] **1.3** 更新 `config.json` 示例
  ```json
  {
    "models_dir": "./models",
    "model_source": {
      "source_type": "auto",
      "local_dir": "./models",
      "network_server": null,
      "official_hub": "ms"
    }
  }
  ```

### Phase 2: 三段式模型加载重构

当前 `ModelSourceConfig.get_model_path()` 已实现三段式，但需要完善：

```
加载顺序:
┌─────────────────┐
│ 1. 本地目录检查  │ → ./models/{model_name}/ 或 STT_MODELS_DIR
└────────┬────────┘
         ↓ (未找到)
┌─────────────────┐
│ 2. 内网服务器    │ → GET {STT_MODEL_SERVER}/models/{model_name}.zip
└────────┬────────┘
         ↓ (服务器不可用或无模型)
┌─────────────────┐
│ 3. 官方源下载    │ → HuggingFace / ModelScope
└─────────────────┘
```

- [ ] **2.1** 完善 `_find_in_local()` 方法
  - 支持嵌套目录: `models/funasr/SenseVoiceSmall/`
  - 支持扁平目录: `models/SenseVoiceSmall/`
  - 验证模型完整性 (检查 `config.yaml` 或 `model.pt`)

- [ ] **2.2** 完善 `_download_from_network()` 方法
  - 添加超时处理 (默认 5s 连接超时)
  - 服务器不可用时静默降级，不报错
  - 下载进度回调 (可选)

- [ ] **2.3** 完善官方源下载
  - 统一下载到 `models/` 目录
  - 支持断点续传 (可选)
  - 下载完成后验证

- [ ] **2.4** 添加模型缓存清理命令
  ```bash
  smartasr models clean      # 清理未使用的模型
  smartasr models list       # 列出已下载模型
  smartasr models download   # 预下载指定模型
  ```

### Phase 3: 初次配置向导

- [ ] **3.1** 创建 `docs/guides/setup.md` 详细配置指南
  ```markdown
  ## 初次配置
  
  ### Step 1: 克隆项目
  git clone https://github.com/xxx/SmartASR.git
  cd SmartASR
  
  ### Step 2: 安装依赖
  pip install -e .[all]  # 完整安装
  # 或
  pip install -e .[api,funasr]  # 只安装 API + FunASR
  
  ### Step 3: 首次运行 (自动下载模型)
  smartasr transcribe test.mp3
  # 模型会自动下载到 ./models/ 目录
  
  ### Step 4: (可选) 配置内网模型服务器
  export STT_MODEL_SERVER=http://192.168.1.100:8765
  ```

- [ ] **3.2** 更新 README.md 添加快速开始链接

- [ ] **3.3** 添加 `smartasr init` 命令
  - 交互式引导配置
  - 创建 `config.json`
  - 检测 FFmpeg
  - 测试引擎可用性

### Phase 4: 模型服务器脚本迁移

- [ ] **4.1** 将模型服务器相关脚本移出项目
  ```
  方案 A: 移到 tools/ 目录 (标记为可选工具)
  方案 B: 创建独立仓库 smartasr-model-server
  方案 C: 保留但添加明确说明
  ```

- [ ] **4.2** 更新 `scripts/README.md` 说明各脚本用途

---

## 涉及文件

| 文件 | 修改内容 |
|------|---------|
| `backend/app/services/stt/compat.py` | 修改 `get_models_dir()` 默认路径 |
| `backend/app/services/stt/config.py` | 完善三段式加载逻辑 |
| `config.example.json` | 更新示例 |
| `README.md` | 添加配置说明 |
| `docs/guides/setup.md` | 新建详细指南 |
| `.gitignore` | 添加 `models/*` |
| `models/.gitkeep` | 新建占位文件 |

---

## 验收标准

1. ✅ 用户克隆后运行 `smartasr transcribe test.mp3` 能自动下载模型到 `./models/`
2. ✅ 配置 `STT_MODEL_SERVER` 后优先从内网下载
3. ✅ 内网服务器不可用时静默降级到官方源
4. ✅ README 有清晰的初次配置步骤
5. ✅ 模型服务器脚本有明确归属说明

---

## 备注

- 当前 `D:\models\funasr\` 是用户本地的模型目录，不是项目的一部分
- `scripts/model_file_server.py` 是给**模型服务器**用的，不是给**客户端**用的
- 三段式加载对用户透明，用户不需要知道模型从哪来
