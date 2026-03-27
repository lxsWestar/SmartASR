# tests/unit/test_dto/

## 本目录职责

单元测试：验证所有 DTO（数据传输对象）类的字段定义、类型校验、默认值及序列化行为。

## 文件清单

| 文件 | 职责 |
|------|------|
| `test_dto.py` | 测试所有 DTO 类及 STANDARD_PARAMS 注册表 |

## 测试覆盖内容

| DTO 类 | 关键测试点 |
|--------|------------|
| `UsageInfo` | 音频时长/处理时间字段 |
| `STTRequest` | `params` + `engine_options` 双层结构，字段互不干扰 |
| `STTSegment` | 时间戳字段可选性，文本字段必填性 |
| `STTResponse` | segments 列表、usage 嵌套 |
| `ParameterSpec` | `layer` 字段取值（`"standard"` 或 `"engine"`） |
| `ModelInfo` | 模型元信息字段完整性 |
| `EngineMetadata` | 引擎元数据结构 |
| `STANDARD_PARAMS` | 注册表包含 5 个标准参数 |

## 重要：双层参数架构（最近变更）

`STTRequest.options` 已拆分为两个字段，**务必基于新结构写测试**：

```python
# ✅ 新架构
class STTRequest(BaseModel):
    params: dict          # 标准层：itn, timestamps, language 等 SmartASR 统一参数
    engine_options: dict  # 直通层：原样透传给引擎 SDK

# ❌ 旧架构（已废弃，不得恢复）
class STTRequest(BaseModel):
    options: dict
```

## STANDARD_PARAMS 注册表

必须包含且仅包含以下 5 个标准参数：

| 参数名 | Layer |
|--------|-------|
| `itn` | `"standard"` |
| `timestamps` | `"standard"` |
| `context` | `"standard"` |
| `speaker_diarization` | `"standard"` |
| `max_speakers` | `"standard"` |

## ParameterSpec.layer 字段

```python
# 合法值
layer: Literal["standard", "engine"]

# ❌ 不得使用其他字符串
layer = "std"      # 错误
layer = "Standard" # 错误（大小写敏感）
```

## 设计约束（AI 必读）

1. **DTO 定义在 `backend/app/models/dto.py`（或同等路径）**，测试只验证行为，不在此修改 DTO
2. **`params` 和 `engine_options` 是相互独立的字段**，测试应验证两者不会互相影响
3. **Pydantic 校验测试**：传入非法类型时必须抛出 `ValidationError`，用 `pytest.raises` 捕获

## 运行命令

```bash
pytest tests/unit/test_dto/ -v
```

## 上下游关系

```
[测试目标] backend/app/models/dto.py（所有 DTO 类）
[不依赖] 引擎、数据库、外部服务
```
