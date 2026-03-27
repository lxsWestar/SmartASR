# tests/unit/test_audio_utils/

## 本目录职责

单元测试：验证 `backend/app/utils/audio.py` 中音频工具函数的正确性，**全程 Mock FFmpeg，无真实文件操作**。

## 文件清单

| 文件 | 职责 |
|------|------|
| `test_audio_utils.py` | 测试所有音频工具函数 |

## 测试覆盖内容

| 测试目标 | 测试要点 |
|----------|----------|
| `check_ffmpeg()` | FFmpeg 可用/不可用时的返回值 |
| `convert_to_16k_wav()` | 正常转换、FFmpeg 失败、格式不支持 |
| `get_duration()` | 正常获取时长、文件不存在、FFmpeg 异常 |
| `SUPPORTED_FORMATS` | 格式列表包含预期格式（mp3/wav/m4a 等） |

## 设计约束（AI 必读）

> ⚠️ **最容易犯的错误**

1. **单元测试严禁调用真实 FFmpeg**——必须用 `unittest.mock.patch` Mock 所有 subprocess 调用
2. **严禁在测试中创建真实音频文件**——用 `tmp_path` fixture 或 Mock 文件对象替代
3. **`SUPPORTED_FORMATS` 是常量**，测试只验证其包含预期值，不要在测试中修改它
4. **FFmpeg 路径在不同 OS 不同**——Mock `subprocess.run` 而非特定路径

## Mock 示例

```python
from unittest.mock import patch, MagicMock

def test_check_ffmpeg_available():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        assert check_ffmpeg() is True

def test_check_ffmpeg_not_found():
    with patch("subprocess.run", side_effect=FileNotFoundError):
        assert check_ffmpeg() is False
```

## 运行命令

```bash
pytest tests/unit/test_audio_utils/ -v
```

## 上下游关系

```
[测试目标] backend/app/utils/audio.py
[Mock 对象] subprocess.run（FFmpeg 调用）
[不依赖] 真实音频文件、FFmpeg 安装
```
