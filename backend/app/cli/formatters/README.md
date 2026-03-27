# backend/app/cli/formatters/

## 本目录职责

将 `STTResponse` 对象序列化为不同文本格式，供 CLI 输出或文件保存。每个格式化器是**无副作用的纯函数封装**。

## 文件清单

| 文件 | 类名 | 格式 | 扩展名 | 特点 |
|------|------|------|--------|------|
| `base.py` | `OutputFormatter` | — | — | 抽象基类，定义统一接口 |
| `txt.py` | `TxtFormatter` | 纯文本 | `.txt` | 仅含转写文本，无时间戳 |
| `json_fmt.py` | `JsonFormatter` | JSON | `.json` | 完整元数据，含置信度/时间戳 |
| `srt.py` | `SrtFormatter` | SRT 字幕 | `.srt` | 视频字幕格式，需要分段时间戳 |
| `vtt.py` | `VttFormatter` | WebVTT 字幕 | `.vtt` | Web 字幕格式，需要分段时间戳 |
| `tsv.py` | `TsvFormatter` | 制表符分隔 | `.tsv` | 表格形式，含开始/结束时间列 |
| `__init__.py` | — | — | — | 导出所有格式化器 |

## 统一接口（OutputFormatter 抽象基类）

```python
class OutputFormatter(ABC):
    name: str        # 格式标识符，如 "srt"、"json"
    extension: str   # 文件扩展名，如 ".srt"、".json"

    @abstractmethod
    def format(self, response: STTResponse) -> str:
        """将 STTResponse 转换为字符串，不得有任何副作用"""
        ...
```

## 设计约束（AI 必读）

> ⚠️ **最容易犯的错误**

1. **格式化器禁止写文件**——`format()` 只返回字符串，文件 I/O 由调用方（`commands/transcribe.py`）负责
2. **格式化器禁止调用外部服务**——不得发起网络请求、不得访问数据库
3. **SRT/VTT 格式依赖 `STTSegment` 的时间戳字段**——若 `STTResponse.segments` 为空或无时间戳，需优雅降级（输出空字幕或仅文本），不得抛出异常
4. **新增格式化器必须继承 `OutputFormatter`**，并在 `__init__.py` 中导出，同时在 `commands/transcribe.py` 的格式映射表中注册
5. **`name` 字段值即 CLI 参数值**，命名必须全小写，如 `"srt"`（不是 `"SRT"`）

## SRT / VTT 时间格式说明

```
SRT: 00:00:01,000 --> 00:00:03,500   （毫秒用逗号）
VTT: 00:00:01.000 --> 00:00:03.500   （毫秒用点）
```

## 上下游关系

```
[上游] backend/app/cli/commands/transcribe.py
    → 根据 -f/--format 参数选择格式化器实例，调用 .format(response)

[下游] 无
    → 纯字符串返回，不依赖任何外部模块
```
