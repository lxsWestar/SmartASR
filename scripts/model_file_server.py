"""
model_file_server.py - 本地模型文件服务器
==========================================

作用: 将本地模型目录作为 HTTP 服务器，供其他机器下载模型
维护: AI + Human

用法:
    python scripts/model_file_server.py --port 8001 --models-dir D:/models/funasr

其他机器配置:
    设置环境变量 STT_MODEL_SERVER=http://你的IP:8001
    或在 config.json 中设置 model_source.network_server
"""

import argparse
import os
import zipfile
import tempfile
import shutil
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from functools import partial
import urllib.parse
import json


class ModelFileHandler(SimpleHTTPRequestHandler):
    """模型文件服务 Handler"""
    
    def __init__(self, *args, models_dir: Path, **kwargs):
        self.models_dir = models_dir
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """处理 GET 请求"""
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.strip("/")
        
        # API: /models - 列出所有可用模型
        if path == "models" or path == "":
            self._list_models()
            return
        
        # API: /models/{model_name} - 返回模型信息
        if path.startswith("models/") and not path.endswith(".zip"):
            model_name = path.split("/")[1]
            self._model_info(model_name)
            return
        
        # API: /models/{model_name}.zip - 下载模型压缩包
        if path.startswith("models/") and path.endswith(".zip"):
            model_name = path.split("/")[1].replace(".zip", "")
            self._download_model(model_name)
            return
        
        # API: /health - 健康检查
        if path == "health":
            self._send_json({"status": "ok", "models_dir": str(self.models_dir)})
            return
        
        # 默认: 404
        self.send_error(404, f"Not Found: {path}")
    
    def _list_models(self):
        """列出所有可用模型"""
        models = []
        for item in self.models_dir.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                # 检查是否是有效模型目录 (包含 config.yaml 或 model.pt)
                is_valid = any((item / f).exists() for f in ["config.yaml", "model.pt", "configuration.json"])
                if is_valid:
                    size = sum(f.stat().st_size for f in item.rglob("*") if f.is_file())
                    models.append({
                        "name": item.name,
                        "size_mb": round(size / (1024 * 1024), 2),
                        "download_url": f"/models/{item.name}.zip",
                    })
        
        self._send_json({
            "models": models,
            "total": len(models),
            "models_dir": str(self.models_dir),
        })
    
    def _model_info(self, model_name: str):
        """返回模型详细信息"""
        model_dir = self.models_dir / model_name
        
        if not model_dir.exists() or not model_dir.is_dir():
            self.send_error(404, f"Model not found: {model_name}")
            return
        
        # 收集文件列表
        files = []
        total_size = 0
        for f in model_dir.rglob("*"):
            if f.is_file():
                rel_path = f.relative_to(model_dir)
                size = f.stat().st_size
                files.append({
                    "path": str(rel_path),
                    "size": size,
                })
                total_size += size
        
        # 读取配置信息
        config = {}
        config_file = model_dir / "config.yaml"
        if config_file.exists():
            try:
                import yaml
                with open(config_file, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
            except:
                pass
        
        self._send_json({
            "name": model_name,
            "path": str(model_dir),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "files": files,
            "config": config,
            "download_url": f"/models/{model_name}.zip",
        })
    
    def _download_model(self, model_name: str):
        """下载模型压缩包"""
        model_dir = self.models_dir / model_name
        
        if not model_dir.exists() or not model_dir.is_dir():
            self.send_error(404, f"Model not found: {model_name}")
            return
        
        # 创建临时 zip 文件
        try:
            # 使用缓存的 zip (如果存在)
            cache_dir = self.models_dir / ".cache"
            cache_dir.mkdir(exist_ok=True)
            zip_path = cache_dir / f"{model_name}.zip"
            
            # 如果缓存不存在或模型更新了，重新打包
            if not zip_path.exists():
                print(f"正在打包模型: {model_name} ...")
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for file in model_dir.rglob("*"):
                        if file.is_file():
                            arcname = f"{model_name}/{file.relative_to(model_dir)}"
                            zf.write(file, arcname)
                print(f"打包完成: {zip_path} ({zip_path.stat().st_size / (1024*1024):.1f} MB)")
            
            # 发送文件
            self.send_response(200)
            self.send_header("Content-Type", "application/zip")
            self.send_header("Content-Disposition", f"attachment; filename={model_name}.zip")
            self.send_header("Content-Length", str(zip_path.stat().st_size))
            self.end_headers()
            
            with open(zip_path, "rb") as f:
                shutil.copyfileobj(f, self.wfile)
                
        except Exception as e:
            self.send_error(500, f"Error creating zip: {e}")
    
    def _send_json(self, data: dict):
        """发送 JSON 响应"""
        content = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(content)
    
    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[{self.log_date_time_string()}] {args[0]}")


def main():
    parser = argparse.ArgumentParser(description="SmartASR 模型文件服务器")
    parser.add_argument("--port", type=int, default=8001, help="服务端口 (默认: 8001)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="监听地址 (默认: 0.0.0.0)")
    parser.add_argument("--models-dir", type=str, default="D:/models/funasr", 
                        help="模型目录 (默认: D:/models/funasr)")
    args = parser.parse_args()
    
    models_dir = Path(args.models_dir)
    if not models_dir.exists():
        print(f"错误: 模型目录不存在: {models_dir}")
        return 1
    
    # 统计模型
    model_count = sum(1 for d in models_dir.iterdir() if d.is_dir() and not d.name.startswith("."))
    
    handler = partial(ModelFileHandler, models_dir=models_dir)
    server = HTTPServer((args.host, args.port), handler)
    
    print("=" * 60)
    print("SmartASR 模型文件服务器")
    print("=" * 60)
    print(f"模型目录: {models_dir}")
    print(f"可用模型: {model_count} 个")
    print(f"服务地址: http://{args.host}:{args.port}")
    print()
    print("API 端点:")
    print(f"  GET /models              - 列出所有模型")
    print(f"  GET /models/{{name}}       - 模型详情")
    print(f"  GET /models/{{name}}.zip   - 下载模型")
    print(f"  GET /health              - 健康检查")
    print()
    print("其他机器配置:")
    print(f"  环境变量: STT_MODEL_SERVER=http://你的IP:{args.port}")
    print("=" * 60)
    print("按 Ctrl+C 停止服务器...")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止")
    
    return 0


if __name__ == "__main__":
    exit(main())
