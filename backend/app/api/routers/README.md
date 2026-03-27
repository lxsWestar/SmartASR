# backend/app/api/routers/

## 本目录职责

定义所有 HTTP API 路由处理器，挂载在 `/api/stt/` 前缀下（前缀由上层 `router.py` 统一注入，**路由文件内不重复写**）。

## 文件清单

| 文件 | 路由前缀 | 职责 |
|------|----------|------|
| `transcribe.py` | `/audio/transcriptions` | 核心转写接口，同步/异步模式 |
| `engines.py` | `/engines` | 查询可用引擎列表及引擎详情 |
| `tasks.py` | `/tasks` | 异步任务状态查询与结果获取 |
| `files.py` | `/files` | 上传文件管理（临时文件生命周期） |
| `health.py` | `/health` | 健康检查，无鉴权 |
| `config_api.py` | `/config` | 运行时配置读取（只读） |
| `__init__.py` | — | 包标识，通常为空 |

## 核心路由：transcribe.py

```
POST /audio/transcriptions
  ?async=false（默认）→ 同步处理，返回 200 + STTResponse
  ?async=true         → 异步入队，返回 202 + {"task_id": "..."}
```

### 双层参数架构

```json
{
  "params": {
    "itn": true,
    "timestamps": false,
    "language": "zh"
  },
  "engine_options": {
    "model": "SenseVoiceSmall",
    "batch_size": 4
  }
}
```

- `params`：标准层，SmartASR 统一参数名，引擎适配器负责转换
- `engine_options`：直通层，原样透传给引擎 SDK，不经过校验

## 设计约束（AI 必读）

> ⚠️ **最容易犯的错误**

1. **禁止在路由层直接调用引擎**——必须通过 `backend/app/services/stt/` 服务层，路由只做 HTTP 参数解包和响应组装
2. **禁止在路由文件内写 `/api/stt/` 前缀**——前缀由 `router.py` 的 `include_router(prefix="/api/stt")` 统一注入
3. **错误响应格式固定为** `{"detail": "错误信息"}`——不得使用 `{"error": {...}}` 或其他格式
4. **不得在路由层做业务逻辑判断**（如引擎是否可用、模型是否加载），这是服务层职责
5. 新增路由文件后必须在 `backend/app/api/router.py` 中 `include_router` 注册，否则不生效

## 错误响应规范

```python
# ✅ 正确
raise HTTPException(status_code=400, detail="不支持的音频格式")

# ❌ 错误
return {"error": {"code": 400, "message": "..."}}
```

## 上下游关系

```
[上游] backend/app/api/router.py
    → include_router 挂载本目录所有路由，注入 /api/stt/ 前缀

[下游] backend/app/services/stt/
    → 路由调用服务层执行实际转写逻辑

[下游] backend/app/tasks/
    → async=true 模式下，路由调用任务管理器入队
```
