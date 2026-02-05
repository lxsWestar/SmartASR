# scripts/ - 工具脚本

> 运维、部署及工具类脚本

## 目录结构

```
scripts/
├── README.md                           # 本文件
├── download_sensevoice.py              # SenseVoice 完整下载脚本
├── download_sensevoice_small_files.py  # SenseVoiceSmall 下载脚本
├── download_cosyvoice2_small_files.py  # CosyVoice2 下载脚本 (TTS，非必需)
├── model_server.py                     # [服务端] 模型HTTP服务 (简单版)
└── model_file_server.py                # [服务端] 模型HTTP服务 (完整版)
```

## ⚠️ 重要说明

### 客户端 vs 服务端脚本

| 脚本 | 类型 | 说明 |
|------|------|------|
| `download_*.py` | **客户端** | 下载模型到本地，SmartASR 用户使用 |
| `model_server.py` | **服务端** | 给内网其他机器提供模型下载，运维人员使用 |
| `model_file_server.py` | **服务端** | 同上，功能更完整 |

**服务端脚本不是必须的**，只有在以下场景才需要：
- 公司内网部署，需要一台机器作为模型服务器
- 离线环境分发预下载的模型

如果你只是个人使用 SmartASR，无需关心服务端脚本。

---

## 客户端脚本

在内网提供模型下载服务，让其他机器可以快速获取预下载的模型。

**使用场景：**
- 公司内网部署，避免每台机器都从外网下载
- 离线环境，预先下载好模型后分发

**启动服务：**
```bash
python scripts/model_server.py --models-dir D:\models\funasr --port 8765
```

**客户端配置：**
```powershell
$env:STT_MODEL_SERVER = "http://192.168.1.100:8765"
```

**API 端点：**
| 端点 | 说明 |
|------|------|
| `GET /` | 列出所有可用模型 |
| `GET /models/{name}` | 下载指定模型 (zip 格式) |
| `GET /health` | 健康检查 |

### download_sensevoice_small_files.py - 模型下载脚本

从 ModelScope 下载 SenseVoiceSmall 模型，小文件自动下载，大文件提供直链供手动下载。

```bash
python scripts/download_sensevoice_small_files.py
```

## 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `STT_MODELS_DIR` | 本地模型目录 | 系统缓存目录 |
| `STT_MODEL_SERVER` | 内网模型服务地址 | 无 |
