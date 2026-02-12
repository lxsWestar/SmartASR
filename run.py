#!/usr/bin/env python
"""
启动 SmartASR API 服务的快捷入口

使用方式:
    python run.py
    python run.py --port 8080
    python run.py --reload
"""
import sys
from pathlib import Path

# 确保项目根目录在 Python 路径中
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    import uvicorn
    
    # 默认参数
    host = "0.0.0.0"
    port = 8000
    reload = False
    
    # 简单参数解析
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--port" and i + 1 < len(args):
            port = int(args[i + 1])
            i += 2
        elif args[i] == "--host" and i + 1 < len(args):
            host = args[i + 1]
            i += 2
        elif args[i] == "--reload":
            reload = True
            i += 1
        else:
            i += 1
    
    print("\n🚀 SmartASR API 服务启动中...")
    print(f"📍 访问地址: http://localhost:{port}")
    print(f"📚 API 文档: http://localhost:{port}/documents")
    print("❌ 按 Ctrl+C 停止服务\n")
    
    uvicorn.run(
        "backend.app.api.main:app",
        host=host,
        port=port,
        reload=reload,
    )
