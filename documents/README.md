# documents/ - 文档目录

> 存放 SmartASR 项目的所有用户文档

## 职责
为开发者和用户提供完整的项目文档，包括 API 参考、使用指南和设计文档。

## 目录结构
```
documents/
├── README.md              # 本文件 (文档索引)
│
├── api/                   # API 文档
│   ├── README.md          # API 概述
│   └── API_CONNECTIONS.md # API 连接说明
│
├── design/                # 设计文档
│   └── architecture.md    # 架构设计
│
└── guides/                # 使用指南
    ├── quickstart.md      # 快速开始
    ├── embedding.md       # 嵌入其他项目
    └── engines.md         # 引擎开发指南
```

## 文档分类

### api/ - API 文档
**目标读者**: API 调用者、前端开发者
**内容**:
- RESTful API 端点说明
- 请求/响应格式
- 错误码说明
- 认证方式

### design/ - 设计文档
**目标读者**: 核心开发者、架构师
**内容**:
- 系统架构图
- 模块职责划分
- 技术选型理由
- 扩展点说明

### guides/ - 使用指南
**目标读者**: 所有用户
**内容**:
- 快速开始教程
- 嵌入集成指南
- 引擎开发教程
- 常见问题解答

## 快速链接

| 文档 | 说明 | 适合谁 |
|------|------|--------|
| [快速开始](guides/quickstart.md) | 5 分钟上手 | 新用户 |
| [API 参考](api/README.md) | 完整 API 说明 | 开发者 |
| [嵌入指南](guides/embedding.md) | 集成到其他项目 | 集成开发者 |
| [引擎开发](guides/engines.md) | 开发新引擎 | 贡献者 |
| [架构设计](design/architecture.md) | 系统设计 | 架构师 |

## 上下游关系
```
引用来源:
  ├── TODO.md (开发计划)
  ├── AGENTS.md (AI 协作规范)
  └── 代码注释

被引用:
  ├── README.md (项目根目录)
  └── 外部用户
```

## 文档编写规范

### Markdown 格式
- 使用 ATX 风格标题 (`#`, `##`, `###`)
- 代码块标注语言 (```python, ```bash)
- 表格对齐使用 `:---`, `:---:`, `---:`

### 命名规范
- 文件名: 小写 + 连字符 (`quick-start.md`)
- 标题: 动词开头 (`安装依赖`, `配置环境`)

### 代码示例
```python
# ✅ 好的示例: 完整可运行
from stt import transcribe
result = transcribe("audio.mp3")
print(result.text)

# ❌ 差的示例: 省略关键部分
result = transcribe(...)  # 不清楚参数
```

## 文档状态

| 文档 | 状态 | 最后更新 |
|------|------|----------|
| quickstart.md | 🔲 待完善 | - |
| embedding.md | 🔲 待完善 | - |
| engines.md | 🔲 待完善 | - |
| architecture.md | 🔲 待完善 | - |
| API_CONNECTIONS.md | ✅ 已有 | 2026-01-23 |
