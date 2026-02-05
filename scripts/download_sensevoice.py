"""
下载 SenseVoice 模型（带进度条）

用法:
    python scripts/download_sensevoice.py
"""

from modelscope import snapshot_download
from pathlib import Path

# 目标目录
target_dir = Path(r"D:\models\funasr")
target_dir.mkdir(parents=True, exist_ok=True)

print("开始下载 SenseVoiceSmall 模型...")
print(f"保存位置: {target_dir}")
print("-" * 60)

# 下载模型（自动显示进度）
model_dir = snapshot_download(
    'iic/SenseVoiceSmall',
    cache_dir=str(target_dir),
    revision='master',
)

print("-" * 60)
print(f"✅ 下载完成！")
print(f"模型位置: {model_dir}")
print("\n设置环境变量使用:")
print(f'$env:STT_MODELS_DIR = "{target_dir}"')
