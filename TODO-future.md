# SmartASR: 后续扩展与部署计划

> 🚀 本文件记录初期范围之外的扩展计划和部署方案。

---

## 一、更多引擎 (计划中)

| 引擎 | 类型 | 优先级 | 状态 | 说明 |
|------|------|--------|------|------|
| Faster-Whisper | 本地 | 高 | 🔲 | OpenAI Whisper 加速版，多语言 |
| OpenAI Whisper API | 云端 | 高 | 🔲 | 官方 API，高精度 |
| Google Cloud STT | 云端 | 中 | 🔲 | 企业级，多语言 |
| Azure Speech | 云端 | 中 | 🔲 | 微软云，实时转写 |
| Deepgram | 云端 | 中 | 🔲 | 企业级 API |
| AssemblyAI | 云端 | 低 | 🔲 | 新兴 API |

### 添加新引擎步骤
```bash
# 1. 复制模板
cp backend/app/services/stt/engines/_template.py \
   backend/app/services/stt/engines/whisper.py

# 2. 实现引擎类
# 3. 安装依赖: pip install faster-whisper
# 4. 完成！引擎自动注册
```

---

## 二、高级功能 (未来版本)

### 2.1 流式识别 WebSocket
- [ ] WebSocket 端点 `/ws/stt/stream`
- [ ] 实时音频流输入
- [ ] 实时文字输出
- [ ] 支持断点续传

```
客户端 → WebSocket → 音频流 → 实时识别 → 文字流 → 客户端
```

### 2.2 说话人分离 (Diarization)
- [ ] 识别多个说话人
- [ ] 为每段文字标记说话人 ID
- [ ] 支持会议转写场景

```json
{
  "segments": [
    {"speaker": "SPEAKER_01", "text": "你好", "start_ms": 0, "end_ms": 1000},
    {"speaker": "SPEAKER_02", "text": "你好", "start_ms": 1200, "end_ms": 2000}
  ]
}
```

### 2.3 实时字幕
- [ ] 低延迟模式
- [ ] 滑动窗口识别
- [ ] 字幕格式直出 (SRT/VTT)

### 2.4 多文件合并识别
- [ ] 上传多个音频文件
- [ ] 按顺序合并识别
- [ ] 保持时间戳连续

### 2.5 热词增强
- [ ] 自定义热词表
- [ ] 提高专业术语识别率
- [ ] 支持动态更新

---

## 三、跨平台嵌入指南

### 方式 A: pip 安装 (推荐)
```bash
# 未来发布到 PyPI 后
pip install SmartASR

# 或从 Git 安装
pip install git+https://github.com/xxx/SmartASR.git
```

### 方式 B: 复制目录嵌入
```bash
# 1. 复制核心目录到你的项目
cp -r SmartASR/stt your_project/services/

# 2. 只保留需要的引擎
rm your_project/services/stt/engines/ali_qwen.py  # 不需要云端引擎

# 3. 安装引擎依赖
pip install funasr  # 只装你用的引擎依赖
```

### 方式 C: 作为独立服务
```bash
# 启动 HTTP 服务
python -m SmartASR.server --host 0.0.0.0 --port 8080

# Docker 方式
docker run -p 8080:8080 SmartASR/server
```

### 嵌入后的使用
```python
# Python 库方式调用
from your_project.services.stt import transcribe, list_engines

# 查看可用引擎
engines = list_engines()
print(engines)  # [{'name': 'ali_funasr', ...}]

# 识别音频
result = transcribe(
    audio_path="test.mp3",
    engine="ali_funasr",
    model="SenseVoiceSmall"
)
print(result.text)
```

---

## 四、部署方案

### 4.1 Docker 容器化
```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY . .

RUN pip install -e ".[all]"

EXPOSE 8000
CMD ["python", "-m", "backend.app.cli", "serve", "--host", "0.0.0.0"]
```

```bash
# 构建和运行
docker build -t smartasr:latest .
docker run -p 8000:8000 -v /path/to/models:/app/models smartasr:latest
```

### 4.2 Docker Compose
```yaml
# docker-compose.yml
version: '3.8'

services:
  smartasr:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./models:/app/models
      - ./uploads:/app/uploads
    environment:
      - STT_MODELS_DIR=/app/models
      - CUDA_VISIBLE_DEVICES=0
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

### 4.3 Kubernetes Helm Chart
```yaml
# values.yaml
replicaCount: 2

image:
  repository: smartasr
  tag: latest

resources:
  limits:
    nvidia.com/gpu: 1
    memory: 8Gi
  requests:
    memory: 4Gi

persistence:
  models:
    enabled: true
    size: 20Gi
```

### 4.4 Serverless 部署

#### AWS Lambda
```python
# handler.py
from backend.app.services.stt import transcribe

def lambda_handler(event, context):
    audio_url = event['audio_url']
    # 下载音频到 /tmp
    # 调用 transcribe
    return {"text": result.text}
```

#### 阿里云函数计算
```python
# index.py
import fc2

def handler(event, context):
    # 从 OSS 获取音频
    # 调用 transcribe
    # 返回结果
    pass
```

---

## 五、监控与运维

### 5.1 Prometheus 指标
```
# HELP stt_tasks_total Total transcription tasks
# TYPE stt_tasks_total counter
stt_tasks_total{engine="ali_funasr",status="completed"} 145
stt_tasks_total{engine="ali_funasr",status="failed"} 3

# HELP stt_task_duration_seconds Task processing duration
# TYPE stt_task_duration_seconds histogram
stt_task_duration_seconds_bucket{engine="ali_funasr",le="1"} 10
stt_task_duration_seconds_bucket{engine="ali_funasr",le="5"} 50

# HELP stt_model_memory_bytes Memory usage by model
# TYPE stt_model_memory_bytes gauge
stt_model_memory_bytes{engine="ali_funasr",model="SenseVoiceSmall"} 1258291200
```

### 5.2 Grafana Dashboard
- 任务吞吐量
- 平均处理时间
- GPU 显存使用
- 错误率趋势

### 5.3 日志聚合
- 结构化 JSON 日志
- ELK Stack / Loki 集成
- 请求追踪 (request_id)

---

## 六、安全加固

### 6.1 API 认证
- [ ] API Key 认证
- [ ] JWT Token 支持
- [ ] OAuth2 集成

### 6.2 速率限制
- [ ] 请求频率限制
- [ ] 并发连接限制
- [ ] 文件大小限制

### 6.3 数据安全
- [ ] 音频文件加密存储
- [ ] 自动清理临时文件
- [ ] 审计日志

---

## 七、性能优化

### 7.1 模型优化
- [ ] 模型量化 (INT8/FP16)
- [ ] ONNX Runtime 推理
- [ ] TensorRT 加速

### 7.2 并发优化
- [ ] 批量推理
- [ ] 请求队列
- [ ] 自动扩缩容

### 7.3 缓存策略
- [ ] 模型预加载
- [ ] 结果缓存 (相同音频)
- [ ] 分布式缓存 (Redis)
