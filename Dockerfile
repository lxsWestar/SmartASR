FROM python:3.12-slim

# 系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 先复制依赖声明，利用 Docker layer 缓存
COPY pyproject.toml .
COPY README.md .

# 安装 PyTorch (CPU) + 核心引擎依赖
# qwen-asr 要求 transformers>=4.51，与 funasr 可能有冲突；分两步安装
RUN pip install --no-cache-dir \
        torch torchaudio \
        --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -e ".[api,funasr]" && \
    pip install --no-cache-dir qwen-asr soundfile

# 复制应用代码
COPY backend/ ./backend/

# 复制本地模型（仅在模型目录存在且非空时有效）
# 如果模型很大不想打进镜像，可通过 volume mount 挂载，并设置 STT_MODELS_DIR
COPY models/ /data/models/

EXPOSE 8000

ENV STT_MODELS_DIR=/data/models

CMD ["uvicorn", "backend.app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
