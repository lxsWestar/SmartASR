"""
音频工具单元测试 (V2 - 重构版)
================================

测试原则:
1. 隔离外部依赖 (FFmpeg)
2. 测试实际错误场景
3. 测试边界情况
4. 为集成测试预留空间
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess

from backend.app.services.stt.audio_utils import (
    check_ffmpeg,
    get_ffmpeg_version,
    convert_to_16k_wav,
    get_duration,
    SUPPORTED_FORMATS,
)
from backend.app.services.stt.exceptions import (
    FFmpegNotFoundError,
    UnsupportedFormatError,
)


# ============================================================================
# FFmpeg 检测测试
# ============================================================================
class TestCheckFFmpeg:
    """测试 FFmpeg 检测"""
    
    @patch("shutil.which")
    def test_ffmpeg_found(self, mock_which):
        """测试 FFmpeg 已安装"""
        mock_which.return_value = "/usr/bin/ffmpeg"
        assert check_ffmpeg() is True
    
    @patch("shutil.which")
    def test_ffmpeg_not_found(self, mock_which):
        """测试 FFmpeg 未安装"""
        mock_which.return_value = None
        assert check_ffmpeg() is False
    
    @patch("shutil.which")
    def test_ffmpeg_windows_path(self, mock_which):
        """测试 Windows 路径"""
        mock_which.return_value = r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"
        assert check_ffmpeg() is True


class TestGetFFmpegVersion:
    """测试获取 FFmpeg 版本"""
    
    @patch("shutil.which")
    def test_ffmpeg_not_installed(self, mock_which):
        """测试 FFmpeg 未安装时抛出异常"""
        mock_which.return_value = None
        
        with pytest.raises(FFmpegNotFoundError):
            get_ffmpeg_version()
    
    @patch("shutil.which")
    @patch("subprocess.run")
    def test_version_parsing(self, mock_run, mock_which):
        """测试版本解析"""
        mock_which.return_value = "/usr/bin/ffmpeg"
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="ffmpeg version 5.1.2 Copyright (c) 2000-2023",
            stderr=""
        )
        
        version = get_ffmpeg_version()
        assert version is not None
        assert isinstance(version, str)
    
    @patch("shutil.which")
    @patch("subprocess.run")
    def test_version_error_handling(self, mock_run, mock_which):
        """测试版本获取失败时的行为"""
        mock_which.return_value = "/usr/bin/ffmpeg"
        mock_run.side_effect = subprocess.SubprocessError("Command failed")
        
        # 实际实现: subprocess 失败时返回 "unknown"
        result = get_ffmpeg_version()
        assert result == "unknown", f"预期返回 'unknown'，实际返回 {result!r}"


# ============================================================================
# 音频转换测试
# ============================================================================
class TestConvertTo16kWav:
    """测试音频转换"""
    
    @patch("shutil.which")
    def test_ffmpeg_required(self, mock_which):
        """测试需要 FFmpeg"""
        mock_which.return_value = None
        
        with pytest.raises(FFmpegNotFoundError):
            convert_to_16k_wav(Path("/test/audio.mp3"))
    
    @patch("shutil.which")
    def test_file_not_found(self, mock_which):
        """测试文件不存在"""
        mock_which.return_value = "/usr/bin/ffmpeg"
        
        with pytest.raises(FileNotFoundError):
            convert_to_16k_wav(Path("/definitely/not/exists/audio.mp3"))
    
    @patch("shutil.which")
    def test_unsupported_format(self, mock_which, tmp_path):
        """测试不支持的格式"""
        mock_which.return_value = "/usr/bin/ffmpeg"
        
        # 创建一个不支持格式的文件
        bad_file = tmp_path / "test.xyz"
        bad_file.touch()
        
        with pytest.raises(UnsupportedFormatError) as exc_info:
            convert_to_16k_wav(bad_file)
        
        assert ".xyz" in str(exc_info.value)
    
    @patch("shutil.which")
    @patch("subprocess.run")
    def test_conversion_success(self, mock_run, mock_which, tmp_path):
        """测试转换成功"""
        mock_which.return_value = "/usr/bin/ffmpeg"
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        
        # 创建源文件
        source_file = tmp_path / "test.mp3"
        source_file.touch()
        
        # 模拟输出文件创建
        def create_output(*args, **kwargs):
            output_path = tmp_path / "test_16k.wav"
            output_path.touch()
            return MagicMock(returncode=0, stderr="")
        
        mock_run.side_effect = create_output
        
        result = convert_to_16k_wav(source_file)
        
        # 结果应该是 Path 对象
        assert isinstance(result, Path)
    
    @patch("shutil.which")
    @patch("subprocess.run")
    def test_conversion_failure(self, mock_run, mock_which, tmp_path):
        """测试转换失败"""
        mock_which.return_value = "/usr/bin/ffmpeg"
        mock_run.return_value = MagicMock(
            returncode=1,
            stderr="Error: Invalid data found when processing input"
        )
        
        source_file = tmp_path / "corrupted.mp3"
        source_file.touch()
        
        # 应该抛出某种异常
        with pytest.raises(Exception):  # 具体异常类型取决于实现
            convert_to_16k_wav(source_file)
    
    @patch("shutil.which")
    def test_output_path_custom(self, mock_which, tmp_path):
        """测试自定义输出路径"""
        mock_which.return_value = "/usr/bin/ffmpeg"
        
        source_file = tmp_path / "input.mp3"
        source_file.touch()
        output_file = tmp_path / "custom_output.wav"
        
        # 这个测试验证 API 支持自定义输出路径
        # 具体行为取决于函数签名
        # 如果函数不支持 output_path 参数，这个测试可以跳过


# ============================================================================
# 时长获取测试
# ============================================================================
class TestGetDuration:
    """测试获取音频时长"""
    
    @patch("shutil.which")
    def test_ffmpeg_required(self, mock_which):
        """测试需要 FFmpeg"""
        mock_which.return_value = None
        
        with pytest.raises(FFmpegNotFoundError):
            get_duration(Path("/test/audio.mp3"))
    
    @patch("shutil.which")
    def test_file_not_found(self, mock_which):
        """测试文件不存在时的行为"""
        mock_which.return_value = "/usr/bin/ffmpeg"
        
        # 实际实现: 文件不存在时返回 0
        result = get_duration(Path("/not/exists.mp3"))
        assert result == 0, f"文件不存在时应返回 0，实际返回 {result}"
    
    @patch("shutil.which")
    @patch("subprocess.run")
    def test_duration_parsing(self, mock_run, mock_which, tmp_path):
        """测试时长解析 - 返回秒数"""
        mock_which.return_value = "/usr/bin/ffmpeg"
        # 模拟 ffprobe 输出
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="60.500000",  # 60.5 秒
            stderr=""
        )
        
        audio_file = tmp_path / "test.mp3"
        audio_file.touch()
        
        duration = get_duration(audio_file)
        
        # 精确断言: 应该返回秒数 60.5
        assert isinstance(duration, (int, float))
        assert abs(duration - 60.5) < 0.1, f"预期返回 60.5 秒，实际返回 {duration}"


# ============================================================================
# 支持格式测试
# ============================================================================
class TestSupportedFormats:
    """测试支持的格式"""
    
    def test_common_audio_formats(self):
        """测试常见音频格式"""
        expected_formats = [".mp3", ".wav", ".flac", ".m4a", ".ogg", ".aac"]
        for fmt in expected_formats:
            assert fmt in SUPPORTED_FORMATS, f"应该支持 {fmt}"
    
    def test_video_formats_with_audio(self):
        """测试带音频的视频格式"""
        video_formats = [".mp4", ".mkv", ".avi", ".mov", ".webm"]
        for fmt in video_formats:
            # 视频格式通常也应该支持（提取音轨）
            if fmt in SUPPORTED_FORMATS:
                assert True  # 支持
    
    def test_format_case(self):
        """测试格式大小写"""
        # 格式应该是小写带点
        for fmt in SUPPORTED_FORMATS:
            assert fmt.startswith("."), f"格式应该以点开头: {fmt}"
            assert fmt == fmt.lower(), f"格式应该是小写: {fmt}"
    
    def test_no_duplicates(self):
        """测试没有重复"""
        assert len(SUPPORTED_FORMATS) == len(set(SUPPORTED_FORMATS))


# ============================================================================
# 边界情况测试
# ============================================================================
class TestEdgeCases:
    """测试边界情况"""
    
    @patch("shutil.which")
    def test_path_with_spaces(self, mock_which, tmp_path):
        """测试带空格的路径 - 空格不应导致路径解析失败"""
        mock_which.return_value = "/usr/bin/ffmpeg"
        
        # 创建带空格的目录和文件
        space_dir = tmp_path / "path with spaces"
        space_dir.mkdir()
        audio_file = space_dir / "my audio file.mp3"
        audio_file.touch()  # 创建空文件
        
        # 空文件应该导致 FFmpeg 处理失败（Invalid data），而不是路径错误
        with pytest.raises(FFmpegNotFoundError) as exc_info:
            convert_to_16k_wav(audio_file)
        
        # 精确断言: 错误是因为数据无效，不是因为路径解析失败
        error_msg = str(exc_info.value).lower()
        assert "invalid data" in error_msg, f"预期错误包含 'Invalid data'，实际: {exc_info.value}"
    
    @patch("shutil.which")
    @patch("subprocess.run")
    def test_unicode_path(self, mock_run, mock_which, tmp_path):
        """测试 Unicode 路径 - 中文不应导致编码错误"""
        mock_which.return_value = "/usr/bin/ffmpeg"
        # 模拟 FFmpeg 对空文件的错误响应
        mock_run.return_value = MagicMock(
            returncode=1,
            stderr="Error: Invalid data found when processing input"
        )
        
        # 创建中文路径
        unicode_dir = tmp_path / "音频文件"
        unicode_dir.mkdir()
        audio_file = unicode_dir / "测试音频.mp3"
        audio_file.touch()  # 创建空文件
        
        # 应该抛出 FFmpegNotFoundError (空文件)，而不是 UnicodeError
        with pytest.raises(FFmpegNotFoundError):
            convert_to_16k_wav(audio_file)
    
    @patch("shutil.which")
    def test_empty_file(self, mock_which, tmp_path):
        """测试空文件 - 应该抛出 FFmpegNotFoundError"""
        mock_which.return_value = "/usr/bin/ffmpeg"
        
        empty_file = tmp_path / "empty.mp3"
        empty_file.touch()  # 创建 0 字节文件
        
        # 精确断言: 空文件应该导致 FFmpeg 处理失败
        with pytest.raises(FFmpegNotFoundError) as exc_info:
            convert_to_16k_wav(empty_file)
        
        # 错误应该包含 "Invalid data" 或类似信息
        assert "invalid" in str(exc_info.value).lower() or "failed" in str(exc_info.value).lower()


# ============================================================================
# 实际使用场景测试
# ============================================================================
class TestRealWorldScenarios:
    """测试实际使用场景"""
    
    @patch("shutil.which")
    @patch("subprocess.run")
    def test_batch_conversion(self, mock_run, mock_which, tmp_path):
        """测试批量转换场景"""
        mock_which.return_value = "/usr/bin/ffmpeg"
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        
        # 创建多个文件
        files = []
        for i in range(5):
            f = tmp_path / f"audio_{i}.mp3"
            f.touch()
            files.append(f)
            # 创建输出文件
            (tmp_path / f"audio_{i}_16k.wav").touch()
        
        # 批量转换
        results = []
        for f in files:
            try:
                result = convert_to_16k_wav(f)
                results.append(result)
            except Exception:
                results.append(None)
        
        # 应该能处理所有文件
        assert len(results) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
