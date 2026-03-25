# api/ - RESTful API 服务模块

> **SmartASR API**: FastAPI 构建的语音识别 HTTP 服务

## 职责

提供完整的 RESTful API 接口，支持：
- 同步/异步语音识别
- 引擎与模型管理
- 任务状态查询与管理
- 文件上传与清理
- 配置管理
- 健康检查与监控

## 目录结构

```
api/
├── __init__.py        # 模块入口
├── main.py            # FastAPI 应用入口
└── routers/           # 路由模块 (按功能拆分)
    ├── __init__.py
    ├── transcribe.py  # 转写 API (/api/stt/transcribe)
    ├── engines.py     # 引擎管理 (/api/stt/engines)
    ├── tasks.py       # 任务管理 (/api/stt/tasks)
    ├── files.py       # 文件管理 (/api/stt/files)
    ├── config_api.py  # 配置管理 (/api/stt/config)
    └── health.py      # 健康检查 (/api/stt/health)
```

## 安装依赖

```bash
pip install fastapi uvicorn python-multipart
```

## 启动方式

### 方式 1: 通过 CLI (推荐)
```bash
python -m backend.app.cli serve --host 0.0.0.0 --port 8000
```

### 方式 2: 直接运行
```bash
python -m backend.app.api.main
```

### 方式 3: uvicorn 启动
```bash
uvicorn backend.app.api.main:app --host 0.0.0.0 --port 8000 --reload
```

## API 端点概览

### 转写 API (`routers/transcribe.py`)
| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/stt/transcribe` | 同步识别 (适合短音频) |
| POST | `/api/stt/transcribe/async` | 异步识别 (适合长音频) |

### 引擎管理 (`routers/engines.py`)
| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/stt/engines` | 列出所有引擎 |
| GET | `/api/stt/engines/{name}` | 获取引擎详情 |
| GET | `/api/stt/engines/{name}/models` | 获取引擎模型列表 |
| GET | `/api/stt/engines/{name}/models/{model}` | 获取模型详情 |

### 任务管理 (`routers/tasks.py`)
| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/stt/tasks` | 列出所有任务 |
| GET | `/api/stt/tasks/{id}` | 查询任务状态 |
| DELETE | `/api/stt/tasks/{id}` | 取消/删除任务 |

### 文件管理 (`routers/files.py`)
| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/stt/files` | 列出上传文件 |
| GET | `/api/stt/files/{id}` | 获取文件信息 |
| DELETE | `/api/stt/files/{id}` | 删除文件 |
| POST | `/api/stt/files/cleanup` | 清理过期文件 |
| GET | `/api/stt/files/stats` | 文件统计 |

### 配置管理 (`routers/config_api.py`)
| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/stt/config` | 获取配置 |
| PUT | `/api/stt/config` | 更新配置 |
| GET | `/api/stt/config/api-keys` | 获取 API Key 状态 |
| PUT | `/api/stt/config/api-keys/{engine}` | 设置 API Key |
| DELETE | `/api/stt/config/api-keys/{engine}` | 删除 API Key |

### 健康检查 (`routers/health.py`)
| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/stt/health` | 完整健康状态 |
| GET | `/api/stt/health/simple` | 快速存活检查 |
| GET | `/api/stt/health/ready` | 就绪检查 (K8s) |

## 使用示例

### 同步转写
```bash
curl -X POST http://localhost:8000/api/stt/transcribe \
  -F "file=@audio.mp3" \
  -F "engine=ali_funasr" \
  -F "model=SenseVoiceSmall"
```

响应:
```json
{
  "text": "识别的完整文本",
  "segments": [
    {"start_ms": 0, "end_ms": 2000, "text": "你好"}
  ],
  "duration_ms": 10000,
  "engine": "ali_funasr",
  "model": "SenseVoiceSmall"
}
```

### 异步转写
```bash
# 提交任务
curl -X POST http://localhost:8000/api/stt/transcribe/async \
  -F "file=@long_audio.mp3"

# 响应: {"task_id": "uuid-xxxx", "status": "pending"}

# 查询状态
curl http://localhost:8000/api/stt/tasks/uuid-xxxx
```

### 查看引擎
```bash
curl http://localhost:8000/api/stt/engines
```

### 健康检查
```bash
curl http://localhost:8000/api/stt/health
```

## 上游依赖

```
api/
 └── services/stt/     # STT 核心服务
      ├── registry     # 引擎注册
      ├── dto          # 数据对象
      └── engines/     # 引擎实现
```

## 错误响应格式

```json
{
  "detail": "错误说明（如：引擎 'xxx' 不存在）"
}
```

## 交互式文档

启动服务后访问:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 部署建议

### 生产环境
```bash
# 使用 gunicorn + uvicorn workers
gunicorn backend.app.api.main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  -b 0.0.0.0:8000
```

### Docker
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install -e ".[api]"
EXPOSE 8000
CMD ["python", "-m", "backend.app.cli", "serve", "--host", "0.0.0.0"]
```

## 维护者

- **模块**: API 服务层
- **依赖**: FastAPI, Uvicorn, python-multipart
- **文档**: 详见 [TODO-api.md](../../../TODO-api.md)
