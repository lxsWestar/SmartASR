"""
下载 SenseVoiceSmall 的小文件（排除大文件 model.pt）

大文件 model.pt (~900MB) 请手动下载：
https://www.modelscope.cn/models/iic/SenseVoiceSmall/resolve/master/model.pt

用法:
    python scripts/download_sensevoice_small_files.py
"""

import os
import requests
from pathlib import Path
from tqdm import tqdm

# 目标目录
target_dir = Path(r"D:\models\funasr\SenseVoiceSmall")
target_dir.mkdir(parents=True, exist_ok=True)

# ModelScope 文件列表（排除大文件）
BASE_URL = "https://www.modelscope.cn/models/iic/SenseVoiceSmall/resolve/master"

SMALL_FILES = [
    "config.yaml",
    "configuration.json",
    "chn_jpn_yue_eng_ko_spectok.bpe.model",
    "tokens.json",
    "am.mvn",
    "README.md",
    ".gitattributes",
]

def download_file(url: str, dest: Path):
    """下载单个文件"""
    print(f"下载: {dest.name}")
    
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    total_size = int(response.headers.get('content-length', 0))
    
    with open(dest, 'wb') as f, tqdm(
        total=total_size,
        unit='B',
        unit_scale=True,
        desc=dest.name
    ) as pbar:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                pbar.update(len(chunk))
    
    print(f"✅ {dest.name} 完成")

def main():
    print("=" * 60)
    print("SenseVoiceSmall 小文件下载器")
    print("=" * 60)
    print(f"保存位置: {target_dir}")
    print(f"文件数量: {len(SMALL_FILES)}")
    print()
    
    # 检查 model.pt
    model_pt = target_dir / "model.pt"
    if not model_pt.exists():
        print("⚠️  注意: 大文件 model.pt (~900MB) 需要手动下载")
        print("   下载链接: https://www.modelscope.cn/models/iic/SenseVoiceSmall/resolve/master/model.pt")
        print(f"   保存到: {model_pt}")
        print()
    else:
        print(f"✅ model.pt 已存在 ({model_pt.stat().st_size / (1024**2):.1f} MB)")
        print()
    
    # 下载小文件
    for filename in SMALL_FILES:
        dest = target_dir / filename
        
        if dest.exists():
            print(f"⏭️  跳过: {filename} (已存在)")
            continue
        
        url = f"{BASE_URL}/{filename}"
        
        try:
            download_file(url, dest)
        except Exception as e:
            print(f"❌ 下载失败: {filename}")
            print(f"   错误: {e}")
    
    print()
    print("=" * 60)
    print("✅ 小文件下载完成！")
    print()
    print("下一步：")
    if not model_pt.exists():
        print("  1. 手动下载 model.pt (~900MB)")
        print("  2. 放到:", model_pt)
    else:
        print("  模型已完整，可以使用！")
    print()
    print("设置环境变量:")
    print(f'  $env:STT_MODELS_DIR = "{target_dir.parent}"')
    print("=" * 60)

if __name__ == "__main__":
    main()
