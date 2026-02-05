"""
CosyVoice2-0.5B 模型小文件下载脚本

功能：
1. 列出模型的所有文件及大小
2. 自动下载小于 50MB 的文件
3. 对于大文件，提示用户手动下载的直链

用法：
    python scripts/download_cosyvoice2_small_files.py

目标目录：D:\\models\\cosyvoice2\\CosyVoice2-0.5B
"""

import os
from pathlib import Path
from modelscope.hub.api import HubApi
from modelscope.hub.file_download import model_file_download
from tqdm import tqdm

# 配置
MODEL_ID = "iic/CosyVoice2-0.5B"
LOCAL_DIR = Path("D:/models/cosyvoice2/CosyVoice2-0.5B")
SMALL_FILE_THRESHOLD = 50 * 1024 * 1024  # 50MB

def format_size(size_bytes):
    """格式化文件大小显示"""
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f}KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f}MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f}GB"

def list_model_files():
    """列出模型的所有文件"""
    print(f"📋 正在获取模型文件列表: {MODEL_ID}")
    api = HubApi()
    
    try:
        model_files = api.get_model_files(model_id=MODEL_ID, recursive=True)
        
        print(f"\n找到 {len(model_files)} 个文件：")
        print("-" * 80)
        
        small_files = []
        large_files = []
        
        for file_info in model_files:
            file_path = file_info['Path']
            file_size = file_info.get('Size', 0)
            size_str = format_size(file_size)
            
            if file_size <= SMALL_FILE_THRESHOLD:
                small_files.append((file_path, file_size))
                print(f"  ✅ {file_path:<60} {size_str:>10}")
            else:
                large_files.append((file_path, file_size))
                print(f"  ⚠️  {file_path:<60} {size_str:>10} (需手动下载)")
        
        return small_files, large_files
    
    except Exception as e:
        print(f"❌ 获取文件列表失败: {e}")
        return [], []

def download_small_files(small_files):
    """下载小文件"""
    if not small_files:
        print("\n✅ 没有需要下载的小文件")
        return
    
    print(f"\n📥 开始下载 {len(small_files)} 个小文件到: {LOCAL_DIR}")
    LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    
    success_count = 0
    skip_count = 0
    
    for file_path, file_size in small_files:
        local_file = LOCAL_DIR / file_path
        
        # 检查文件是否已存在且大小正确
        if local_file.exists():
            local_size = local_file.stat().st_size
            if local_size == file_size:
                print(f"  ⏭️  跳过（已存在）: {file_path}")
                skip_count += 1
                continue
        
        # 下载文件
        try:
            print(f"  ⬇️  下载: {file_path} ({format_size(file_size)})")
            local_file.parent.mkdir(parents=True, exist_ok=True)
            
            model_file_download(
                model_id=MODEL_ID,
                file_path=file_path,
                local_dir=str(LOCAL_DIR)
            )
            success_count += 1
            print(f"  ✅ 完成: {file_path}")
        
        except Exception as e:
            print(f"  ❌ 失败: {file_path} - {e}")
    
    print(f"\n📊 下载统计:")
    print(f"  - 成功: {success_count} 个")
    print(f"  - 跳过: {skip_count} 个")

def show_manual_download_info(large_files):
    """显示大文件的手动下载信息"""
    if not large_files:
        print("\n✅ 没有需要手动下载的大文件")
        return
    
    print(f"\n⚠️  需要手动下载 {len(large_files)} 个大文件：")
    print("=" * 80)
    
    total_size = sum(size for _, size in large_files)
    print(f"总大小: {format_size(total_size)}")
    print()
    
    for file_path, file_size in large_files:
        # ModelScope 直链格式
        direct_url = f"https://www.modelscope.cn/api/v1/models/{MODEL_ID}/repo?Revision=master&FilePath={file_path}"
        target_path = LOCAL_DIR / file_path
        
        print(f"📄 文件: {file_path}")
        print(f"   大小: {format_size(file_size)}")
        print(f"   直链: {direct_url}")
        print(f"   目标: {target_path}")
        print()
    
    print("💡 手动下载步骤：")
    print("1. 使用 IDM / 迅雷 / aria2c 等工具复制上面的直链")
    print("2. 下载完成后，将文件移动到对应的目标路径")
    print("3. 验证文件大小是否正确")
    print()

def main():
    print("=" * 80)
    print("CosyVoice2-0.5B 模型下载工具")
    print("=" * 80)
    
    # 1. 列出所有文件
    small_files, large_files = list_model_files()
    
    if not small_files and not large_files:
        print("\n❌ 未找到任何文件")
        return
    
    # 2. 下载小文件
    download_small_files(small_files)
    
    # 3. 显示大文件的手动下载信息
    show_manual_download_info(large_files)
    
    print("\n" + "=" * 80)
    print("✅ 处理完成！")
    print("=" * 80)

if __name__ == "__main__":
    main()
