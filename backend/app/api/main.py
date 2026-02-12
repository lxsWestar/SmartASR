"""
main.py - FastAPI 应用入口
===========================

作用: 创建和配置 FastAPI 应用实例
维护: AI + Human
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import engines, transcribe, tasks, health, config_api, files


def create_app() -> FastAPI:
    """
    创建并配置 FastAPI 应用
    
    Returns:
        FastAPI: 配置好的应用实例
    """
    app = FastAPI(
        title="SmartASR API",
        description="轻量级语音转文字 API 服务",
        version="0.1.0",
        documents_url="/documents",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    
    # CORS 配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 生产环境应限制
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 注册路由
    app.include_router(engines.router, prefix="/api/stt", tags=["引擎管理"])
    app.include_router(transcribe.router, prefix="/api/stt", tags=["语音识别"])
    app.include_router(tasks.router, prefix="/api/stt", tags=["任务管理"])
    app.include_router(health.router, prefix="/api/stt", tags=["健康检查"])
    app.include_router(config_api.router, prefix="/api/stt", tags=["配置管理"])
    app.include_router(files.router, prefix="/api/stt", tags=["文件管理"])
    
    # 简单健康检查 (兼容旧接口)
    @app.get("/health", tags=["系统"])
    async def health_check_legacy():
        """简单健康检查 (兼容接口)"""
        return {"status": "ok", "version": "0.1.0"}
    
    @app.get("/", tags=["系统"])
    async def root():
        """
        根路径 - 返回 API 信息
        """
        return {
            "name": "SmartASR API",
            "version": "0.1.0",
            "documents": "/documents",
            "health": "/api/stt/health",
            "health_simple": "/health",
        }
    
    return app


# 默认应用实例
app = create_app()


if __name__ == "__main__":
    import uvicorn
    print("\n🚀 SmartASR API 服务启动中...")
    print("📍 访问地址: http://localhost:8000")
    print("📚 API 文档: http://localhost:8000/documents")
    print("❌ 按 Ctrl+C 停止服务\n")
    uvicorn.run("backend.app.api.main:app", host="0.0.0.0", port=8000, reload=True)
