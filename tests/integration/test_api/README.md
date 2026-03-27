# tests/integration/test_api/

## 本目录职责

集成测试：使用 FastAPI `TestClient` 测试 HTTP API 端点，**无需真实引擎，可 Mock 引擎层**。

## 文件清单

| 文件 | 状态 | 测试内容 |
|------|------|----------|
| `test_api_endpoints.py` | ⏳ 全部跳过，待实现 | API 端点完整性和响应格式验证 |

## 测试计划（待实现）

| 测试用例 | 端点 | Mock 目标 |
|----------|------|-----------|
| `test_list_engines` | `GET /api/stt/engines` | Mock 引擎注册表 |
| `test_get_engine_info` | `GET /api/stt/engines/{name}` | Mock 引擎元数据 |
| `test_transcribe_sync` | `POST /api/stt/audio/transcriptions` | Mock 服务层返回 STTResponse |
| `test_transcribe_async` | `POST /api/stt/audio/transcriptions?async=true` | Mock 任务队列入队 |
| `test_health_check` | `GET /api/stt/health` | 无需 Mock |
| `test_error_response_format` | 各端点 | 验证错误响应为 `{"detail": "..."}` |

## 运行命令

```bash
pytest tests/integration/test_api/ -v
```

## 设计约束（AI 必读）

> ⚠️ **实现集成测试时的注意事项**

1. **必须使用 `TestClient`，不得启动真实服务**——`from fastapi.testclient import TestClient`
2. **引擎层必须 Mock**——不依赖模型文件是否下载，测试可在 CI 纯环境运行
3. **验证错误响应格式**——所有错误必须返回 `{"detail": "..."}` 格式，这是路由层的契约
4. **必须标记 `@pytest.mark.integration`**，区分于单元测试
5. **与 E2E 的关键区别**：本目录不依赖运行中的服务，用 TestClient 直接调用 ASGI app

## Mock 示例

```python
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from backend.app.api.app import app

client = TestClient(app)

def test_transcribe_sync():
    mock_response = MagicMock()
    mock_response.text = "你好世界"

    with patch("backend.app.services.stt.transcribe_audio", return_value=mock_response):
        resp = client.post("/api/stt/audio/transcriptions", ...)
        assert resp.status_code == 200
```

## 上下游关系

```
[测试目标] backend/app/api/routers/ 下所有路由
[Mock 对象] backend/app/services/stt/（引擎层）
[对比] tests/e2e/ → 需要真实服务和真实引擎
[对比] tests/unit/ → 只测试单个函数/类
```
