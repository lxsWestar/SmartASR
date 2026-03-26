"""
测试 Qwen ASR 引擎识别日语音频

运行前请设置 DASHSCOPE_API_KEY 环境变量：
  set DASHSCOPE_API_KEY=你的API密钥
  python tests/test_qwen_japanese.py

或者传递 API Key 作为参数：
  python tests/test_qwen_japanese.py --api-key YOUR_KEY
"""

import sys
import argparse
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.services.stt.engines.ali_qwen import QwenASREngine
from backend.app.services.stt.dto import STTRequest


def main():
    parser = argparse.ArgumentParser(description="测试 Qwen ASR 日语识别")
    parser.add_argument("--api-key", help="DashScope API Key")
    parser.add_argument(
        "--audio",
        default=r"D:\tmp\fc5270a9e2d0964b40ec0ffec65f2ba6_64k.mp3",
        help="音频文件路径",
    )
    parser.add_argument(
        "--model",
        default="qwen3-asr-flash",
        choices=["qwen3-asr-flash", "qwen3-asr-turbo"],
        help="使用的模型",
    )
    args = parser.parse_args()

    audio_path = Path(args.audio)
    if not audio_path.exists():
        print(f"错误: 音频文件不存在: {audio_path}")
        sys.exit(1)

    print(f"音频文件: {audio_path}")
    print(f"文件大小: {audio_path.stat().st_size / 1024:.1f} KB")
    print(f"使用模型: {args.model}")
    print()

    # 创建引擎
    engine = QwenASREngine()

    # 检查可用性
    ok, msg = engine.check_available()
    if not ok:
        print(f"引擎不可用: {msg}")
        sys.exit(1)
    print(f"引擎状态: {msg}")

    # 构建请求
    options = {}
    if args.api_key:
        options["api_key"] = args.api_key

    request = STTRequest(
        audio_path=audio_path,
        language="ja",  # 日语
        model=args.model,
        engine_options=options,
    )

    print(f"\n开始识别...")
    print("-" * 50)

    try:
        response = engine.transcribe(request)
        
        print(f"\n识别结果:")
        print(f"  引擎: {response.engine}")
        print(f"  模型: {response.model}")
        print(f"  时长: {response.duration_ms / 1000:.2f} 秒")
        print(f"  片段数: {len(response.segments)}")
        
        if response.usage:
            print(f"\n使用统计:")
            print(f"  API 调用次数: {response.usage.api_calls}")
            print(f"  处理耗时: {response.usage.processing_time_ms / 1000:.2f} 秒")
            print(f"  Input Tokens: {response.usage.input_tokens}")
            print(f"  Output Tokens: {response.usage.output_tokens}")
        
        print(f"\n完整文本:")
        print("-" * 50)
        print(response.text)
        print("-" * 50)
        
        print(f"\n分段详情:")
        for i, seg in enumerate(response.segments[:10]):  # 只显示前10个
            time_str = f"{seg.start_ms / 1000:.2f}s - {seg.end_ms / 1000:.2f}s"
            print(f"  [{i+1}] {time_str}: {seg.text}")
        
        if len(response.segments) > 10:
            print(f"  ... 还有 {len(response.segments) - 10} 个片段")
        
        print(f"\n✅ 识别成功!")
        
    except Exception as e:
        print(f"\n❌ 识别失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
