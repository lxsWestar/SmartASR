# tests/integration/test_funasr/

## 本目录职责

集成测试：使用**真实 FunASR 引擎**验证引擎适配器的正确性，需要下载模型文件（首次约 900MB）。

## 文件清单

| 文件 | 职责 |
|------|------|
| `test_funasr_engine.py` | FunASR 引擎完整功能测试 |

## 测试覆盖场景

| 测试用例 | 模型 | 场景 |
|----------|------|------|
| SenseVoiceSmall 中文转写 | `SenseVoiceSmall` | 标准普通话识别 |
| SenseVoiceSmall 日语转写 | `SenseVoiceSmall` | NHK 日语新闻音频 |
| paraformer-zh 转写 | `paraformer-zh` | 替代模型验证 |
| ITN 开启 | `SenseVoiceSmall` | 数字/符号规范化开启 |
| ITN 关闭 | `SenseVoiceSmall` | ITN 关闭对比 |

## 运行前提条件

```
✅ pip install funasr
✅ （可选）安装 torch 以启用 GPU 加速
✅ 首次运行会自动下载模型（SenseVoiceSmall 约 900MB，需网络）
✅ 测试音频文件存在于 tests/fixtures/
```

## 运行命令

```bash
# 运行全部 FunASR 集成测试（默认跳过，需显式指定）
pytest tests/integration/test_funasr/ -v -s

# 仅运行 integration 标记的测试
pytest -m integration -v -s
```

## 默认跳过机制

所有测试用 `@pytest.mark.integration` 标记，在 `pytest.ini` / `conftest.py` 中配置为默认跳过：

```python
@pytest.mark.integration
def test_sensevoice_chinese():
    ...
```

## 设计约束（AI 必读）

> ⚠️ **修改此目录时的注意事项**

1. **不得 Mock FunASR**——本目录存在的意义就是真实引擎测试，Mock 请去 `tests/unit/` 或 `tests/integration/test_api/`
2. **模型路径配置从 `config.json` 读取**，不得在测试中硬编码绝对路径
3. **测试结果断言要宽松**——转写文本可能因模型版本略有差异，断言关键词而非完整字符串
4. **CI 环境默认跳过**——不得将此目录的测试加入默认 CI 流程（模型文件太大）
5. **引擎定义在** `backend/app/services/stt/engines/funasr/`，测试只验证行为，不修改引擎实现

## 上下游关系

```
[测试目标] backend/app/services/stt/engines/funasr/（FunASR 引擎适配器）
[依赖] FunASR 库（真实）+ 模型文件（真实）
[对比] tests/unit/ → Mock 引擎，无需模型文件
```
