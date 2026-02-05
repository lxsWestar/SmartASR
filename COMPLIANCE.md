# 许可证合规审查报告

**生成日期**: 2026-02-05  
**审查范围**: SmartASR 核心代码（`backend/`, `frontend/`, `scripts/`）  
**项目许可证**: MIT License

---

## ✅ 审查结论

SmartASR 核心代码**未直接使用** GPL 代码，可以安全地应用 MIT 许可证用于商业项目。

---

## 📋 代码隔离状态

### 运行时代码（MIT）
- ✅ `backend/` - 核心服务代码，独立实现
- ✅ `frontend/` - 简单的 HTML/JS 前端
- ✅ `scripts/` - 模型下载脚本
- ✅ `tests/` - 测试代码

### 参考代码（GPL v3 - 隔离）
- 📦 `pyvideotrans/` - **仅作参考**，运行时不依赖
  - 代码审查：`backend/` 中无 `import pyvideotrans` 语句 ✅
  - 设计参考：API 结构和引擎抽象参考了其设计思路
  - 实现方式：完全独立重写，无代码复制

---

## 🔍 依赖许可证审查

### Python 核心依赖
| 包名 | 许可证 | 状态 | 备注 |
|------|--------|------|------|
| `typer` | MIT | ✅ | CLI 框架 |
| `pydantic` | MIT | ✅ | 数据验证 |
| `fastapi` | MIT | ✅ | API 框架 |
| `uvicorn` | BSD-3 | ✅ | ASGI 服务器 |
| `httpx` | BSD-3 | ✅ | HTTP 客户端 |

### 可选引擎依赖
| 包名 | 许可证 | 状态 | 备注 |
|------|--------|------|------|
| `funasr` | MIT | ✅ | 阿里 FunASR |
| `dashscope` | Apache-2.0 | ✅ | 通义千问 SDK |
| `torch` | BSD-style | ✅ | PyTorch |
| `faster-whisper` | MIT | ✅ | Whisper 实现 |

**结论**: 所有依赖均为商业友好许可证。

---

## 🛡️ 合规保障措施

### 已实施
1. ✅ 在项目根目录添加 `LICENSE` 文件（MIT）
2. ✅ 在 `README.md` 中明确说明 `pyvideotrans/` 的隔离状态
3. ✅ 在 `.github/instructions/` 添加许可证合规指令
4. ✅ 代码审查：确认无 GPL 代码混入

### 建议步骤（可选）
- [ ] 在生产环境部署时，使用 `.dockerignore` 排除 `pyvideotrans/`
- [ ] 在 PyPI 发布时，`pyproject.toml` 的 `[tool.setuptools]` 中排除该文件夹
- [ ] 定期运行 `pip-licenses` 检查新增依赖的许可证

---

## 📌 法律声明

本文档为技术性合规审查，不构成法律意见。如有疑问，请咨询专业法律顾问。

**参考资料：**
- MIT License: https://opensource.org/licenses/MIT
- GPL v3: https://www.gnu.org/licenses/gpl-3.0.html
- 许可证兼容性: https://www.gnu.org/licenses/license-compatibility.html
