---
applyTo: '**'
---

# 许可证合规指令

## 项目许可证
SmartASR 采用 **MIT License**，可用于商业项目。

## 重要规则

### 1. pyvideotrans/ 隔离原则
- `pyvideotrans/` 文件夹内容为 GPL v3 项目，**仅作参考**
- ❌ 禁止将 `pyvideotrans/` 中的代码复制到 `backend/` 或其他运行时目录
- ❌ 禁止 `backend/` 中的代码导入 `pyvideotrans` 模块
- ✅ 可以参考其设计思路和 API 结构，但必须**独立实现**

### 2. 代码审查
AI 在修改代码时必须确保：
- 所有 `backend/` 代码为原创或使用 MIT 兼容的库
- 不得有 `from pyvideotrans import ...` 语句（测试文件除外）
- 新增依赖必须检查许可证（优先 MIT/Apache 2.0/BSD）

### 3. 依赖许可证白名单
可接受的许可证：
- MIT, Apache 2.0, BSD (2-Clause/3-Clause)
- ISC, PSF (Python Software Foundation)
- LGPL (动态链接，不传染)

需评估的许可证：
- GPL/AGPL (强传染性，避免使用)
- MPL (Mozilla Public License，文件级传染)

### 4. 发布前检查清单
- [ ] 确认没有 GPL 代码混入 `backend/`
- [ ] 所有依赖许可证已审查
- [ ] LICENSE 文件存在于项目根目录
- [ ] README.md 说明了 pyvideotrans/ 的隔离状态
