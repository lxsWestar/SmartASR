# backend/ - 后端代码目录

## 职责
存放 SmartASR 的所有后端业务逻辑代码。

## 目录结构
```
backend/
└── app/
    ├── api/           # FastAPI 路由层
    │   ├── main.py    # 应用入口
    │   └── routers/   # API 端点
    ├── cli/           # 命令行工具 🆕
    │   ├── main.py    # CLI 主程序
    │   ├── commands/  # 子命令
    │   └── formatters/ # 输出格式化
    └── services/
        └── stt/       # STT 核心服务 (可独立嵌入)
```

## 设计思路
- 采用分层架构：`app/services/` 存放业务服务
- `stt/` 目录设计为**可独立复制嵌入**其他项目
- `api/` 存放 FastAPI 路由
- `cli/` 提供命令行界面

## 上下游关系
```
调用方:
  - API 路由层 (未来 app/api/)
  - 命令行工具
  - 外部项目 (嵌入使用)

被调用:
  - 无外部依赖 (核心模块自包含)
```

## 隐含契约
- `stt/` 目录不应依赖 `backend/` 外部的任何代码
- 所有对外接口通过 `stt/__init__.py` 统一导出

## 子目录
- [app/services/stt/README.md](app/services/stt/README.md) - STT 核心模块详细说明
