"""
模型文件服务器
==============

作用: 在内网提供模型下载服务，让其他机器可以快速获取模型。
维护: AI + Human

使用方法:
    # 启动服务 (默认端口 8765)
    python scripts/model_server.py --models-dir D:\\models\\funasr --port 8765
    
    # 客户端配置
    设置环境变量: STT_MODEL_SERVER=http://192.168.1.100:8765

支持的请求:
    GET /                   - 列出所有可用模型
    GET /models             - 同上
    GET /models/{name}      - 下载指定模型 (zip 格式)
    GET /health             - 健康检查
"""

import argparse
import json
import logging
import os
import shutil
import tempfile
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Optional
from urllib.parse import unquote

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)


class ModelServerHandler(SimpleHTTPRequestHandler):
    """模型文件服务处理器"""
    
    models_dir: Path = None  # 类变量，由 main() 设置
    
    def do_GET(self):
        """处理 GET 请求"""
        path = unquote(self.path)
        
        if path == "/" or path == "/models":
            self._list_models()
        elif path == "/health":
            self._health_check()
        elif path.startswith("/models/"):
            model_name = path[8:]  # 去掉 "/models/"
            self._serve_model(model_name)
        else:
            self.send_error(404, "Not Found")
    
    def _list_models(self):
        """列出所有可用模型"""
        models = []
        
        if self.models_dir and self.models_dir.exists():
            for item in self.models_dir.iterdir():
                if item.is_dir() and not item.name.startswith("."):
                    # 计算目录大小
                    size = sum(f.stat().st_size for f in item.rglob("*") if f.is_file())
                    models.append({
                        "name": item.name,
                        "size_mb": round(size / (1024 * 1024), 1),
                        "files": len(list(item.rglob("*"))),
                    })
        
        response = {
            "server": "SmartASR Model Server",
            "models_dir": str(self.models_dir),
            "models": models,
            "total": len(models),
        }
        
        self._send_json(response)
    
    def _health_check(self):
        """健康检查"""
        self._send_json({"status": "ok", "models_dir": str(self.models_dir)})
    
    def _serve_model(self, model_name: str):
        """提供模型下载 (zip 格式)"""
        model_path = self.models_dir / model_name
        
        if not model_path.exists() or not model_path.is_dir():
            self.send_error(404, f"Model not found: {model_name}")
            return
        
        logger.info(f"打包模型: {model_name}")
        
        # 创建临时 zip 文件
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # 打包目录
            shutil.make_archive(tmp_path[:-4], "zip", model_path)
            
            # 发送文件
            zip_path = Path(tmp_path)
            file_size = zip_path.stat().st_size
            
            self.send_response(200)
            self.send_header("Content-Type", "application/zip")
            self.send_header("Content-Disposition", f'attachment; filename="{model_name}.zip"')
            self.send_header("Content-Length", str(file_size))
            self.end_headers()
            
            with open(zip_path, "rb") as f:
                shutil.copyfileobj(f, self.wfile)
            
            logger.info(f"发送完成: {model_name} ({file_size / (1024*1024):.1f} MB)")
            
        finally:
            # 清理临时文件
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def _send_json(self, data: dict):
        """发送 JSON 响应"""
        content = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)
    
    def log_message(self, format, *args):
        """自定义日志格式"""
        logger.info(f"{self.address_string()} - {format % args}")


def main():
    parser = argparse.ArgumentParser(description="SmartASR 模型文件服务器")
    parser.add_argument(
        "--models-dir", "-d",
        type=str,
        default=os.environ.get("STT_MODELS_DIR", "D:\\models\\funasr"),
        help="模型目录路径 (默认: D:\\models\\funasr)",
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8765,
        help="服务端口 (默认: 8765)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="监听地址 (默认: 0.0.0.0)",
    )
    
    args = parser.parse_args()
    
    models_dir = Path(args.models_dir)
    if not models_dir.exists():
        logger.error(f"模型目录不存在: {models_dir}")
        return 1
    
    # 设置类变量
    ModelServerHandler.models_dir = models_dir
    
    # 列出可用模型
    models = [d.name for d in models_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
    logger.info(f"模型目录: {models_dir}")
    logger.info(f"可用模型: {models}")
    
    # 启动服务
    server = HTTPServer((args.host, args.port), ModelServerHandler)
    logger.info(f"服务启动: http://{args.host}:{args.port}")
    logger.info(f"客户端配置: STT_MODEL_SERVER=http://<服务器IP>:{args.port}")
    logger.info("按 Ctrl+C 停止服务")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("服务已停止")
    
    return 0


if __name__ == "__main__":
    exit(main())
