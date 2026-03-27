# tests/e2e/test_full_pipeline/

## 本目录职责

端到端（E2E）测试：验证完整转写流程，从音频文件输入到最终文字输出，覆盖真实引擎和真实服务。

## 文件清单

| 文件 | 状态 | 测试内容 |
|------|------|----------|
| `test_transcribe.py` | ⏳ 全部跳过，待实现 | MP3/WAV/长音频完整流程 |

## 测试计划（待实现）

| 测试用例 | 说明 |
|----------|------|
| `test_mp3_transcription` | 标准 MP3 文件完整转写 |
| `test_wav_transcription` | WAV 文件完整转写 |
| `test_long_audio_pipeline` | 长音频（>5 分钟）分段处理验证 |
| `test_async_transcription` | 异步模式完整流程（提交→轮询→结果） |

## 运行前提条件

E2E 测试对环境要求严格，**缺少任一条件测试将跳过或失败**：

```
✅ 已安装引擎依赖（如 pip install funasr）
✅ 已下载模型文件（SenseVoiceSmall 约 900MB）
✅ SmartASR 服务正在运行（smartasr serve）
✅ tests/fixtures/ 中存在真实音频测试文件
✅ FFmpeg 已安装并在 PATH 中
```

## 运行命令

```bash
# 运行全部 E2E 测试（需满足上述前提）
pytest tests/e2e/ -v -s

# 运行单个测试文件
pytest tests/e2e/test_full_pipeline/test_transcribe.py -v -s
```

## 设计约束（AI 必读）

> ⚠️ **实现 E2E 测试时的注意事项**

1. **E2E 测试不得 Mock 任何引擎或服务层**——Mock 场景归属 `tests/integration/` 或 `tests/unit/`
2. **测试音频文件不得提交到 Git**——在 `conftest.py` 中通过 fixture 下载或跳过
3. **必须用 `@pytest.mark.e2e` 标记**，便于 CI 按需跳过
4. **与 integration 测试的区别**：E2E 需要运行中的服务（真实 HTTP 调用），integration 用 TestClient

## 上下游关系

```
[依赖] 完整运行的 SmartASR 服务（HTTP）
[依赖] 真实引擎（funasr 等）
[依赖] 真实音频文件（fixtures）
[对比] tests/integration/test_api/ → 用 TestClient，无需真实服务
```
