"""
files.py - 文件管理 API
=========================

端点:
- GET /files - 列出已上传的临时文件
- DELETE /files/{file_id} - 手动删除文件
- POST /files/cleanup - 清理过期文件

维护: AI
"""

import logging
import hashlib
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.app.services.stt.compat import get_cache_dir
from backend.app.services.stt.config import get_config

logger = logging.getLogger(__name__)

router = APIRouter()


# ============ 配置 ============

# 文件默认过期时间 (小时)
DEFAULT_EXPIRY_HOURS = 24

# 上传目录名
UPLOAD_DIR_NAME = "uploads"


# ============ Pydantic 模型 ============

class FileInfo(BaseModel):
    """文件信息"""
    file_id: str = Field(..., description="文件唯一标识")
    filename: str = Field(..., description="原始文件名")
    size_mb: float = Field(..., description="文件大小 (MB)")
    uploaded_at: str = Field(..., description="上传时间 (ISO 8601)")
    expires_at: str = Field(..., description="过期时间 (ISO 8601)")
    path: str = Field(..., description="文件路径")
    status: str = Field(default="available", description="状态: available/expired")


class FileListResponse(BaseModel):
    """文件列表响应"""
    files: List[FileInfo] = Field(default_factory=list, description="文件列表")
    total_count: int = Field(..., description="总文件数")
    total_size_mb: float = Field(..., description="总大小 (MB)")
    upload_dir: str = Field(..., description="上传目录")


class FileDeleteResponse(BaseModel):
    """文件删除响应"""
    success: bool
    message: str
    file_id: str


class CleanupRequest(BaseModel):
    """清理请求"""
    before: Optional[str] = Field(
        default=None, 
        description="清理此时间之前的文件 (ISO 8601)"
    )
    max_age_hours: Optional[int] = Field(
        default=None,
        description="清理超过此时长的文件 (小时)"
    )
    status: Optional[str] = Field(
        default=None,
        description="只清理特定状态的文件 (expired/all)"
    )
    dry_run: bool = Field(
        default=False,
        description="预览模式，不实际删除"
    )


class CleanupResponse(BaseModel):
    """清理响应"""
    success: bool
    message: str
    deleted_count: int = Field(..., description="删除的文件数")
    freed_mb: float = Field(..., description="释放的空间 (MB)")
    deleted_files: List[str] = Field(
        default_factory=list, 
        description="删除的文件列表 (dry_run 时为将要删除的)"
    )
    dry_run: bool = Field(default=False, description="是否为预览模式")


# ============ 辅助函数 ============

def _get_upload_dir() -> Path:
    """获取上传目录"""
    upload_dir = get_cache_dir() / UPLOAD_DIR_NAME
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


def _generate_file_id(file_path: Path) -> str:
    """
    根据文件路径生成唯一 ID
    
    使用文件名 + 修改时间生成 hash，确保同一文件返回相同 ID
    """
    stat = file_path.stat()
    content = f"{file_path.name}_{stat.st_mtime}_{stat.st_size}"
    return hashlib.md5(content.encode()).hexdigest()[:16]


def _get_file_info(file_path: Path) -> Optional[FileInfo]:
    """
    获取文件信息
    
    Returns:
        FileInfo 或 None (如果文件不存在或不是普通文件)
    """
    if not file_path.exists() or not file_path.is_file():
        return None
    
    try:
        stat = file_path.stat()
        size_mb = round(stat.st_size / (1024 * 1024), 3)
        
        # 使用文件修改时间作为上传时间
        uploaded_at = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
        expires_at = uploaded_at + timedelta(hours=DEFAULT_EXPIRY_HOURS)
        
        now = datetime.now(timezone.utc)
        status = "expired" if now > expires_at else "available"
        
        return FileInfo(
            file_id=_generate_file_id(file_path),
            filename=file_path.name,
            size_mb=size_mb,
            uploaded_at=uploaded_at.isoformat(),
            expires_at=expires_at.isoformat(),
            path=str(file_path),
            status=status,
        )
    except Exception as e:
        logger.warning(f"无法获取文件信息 {file_path}: {e}")
        return None


def _find_file_by_id(file_id: str) -> Optional[Path]:
    """
    根据 file_id 查找文件
    
    Returns:
        文件路径或 None
    """
    upload_dir = _get_upload_dir()
    
    for file_path in upload_dir.iterdir():
        if file_path.is_file():
            if _generate_file_id(file_path) == file_id:
                return file_path
    
    return None


def _list_all_files(
    status_filter: Optional[str] = None,
    before: Optional[datetime] = None,
    after: Optional[datetime] = None,
) -> List[FileInfo]:
    """
    列出所有文件
    
    Args:
        status_filter: 状态过滤 (available/expired)
        before: 只返回此时间之前上传的文件
        after: 只返回此时间之后上传的文件
    
    Returns:
        FileInfo 列表
    """
    upload_dir = _get_upload_dir()
    files = []
    
    for file_path in upload_dir.iterdir():
        if not file_path.is_file():
            continue
        
        # 跳过隐藏文件和系统文件
        if file_path.name.startswith('.'):
            continue
        
        info = _get_file_info(file_path)
        if info is None:
            continue
        
        # 状态过滤
        if status_filter and info.status != status_filter:
            continue
        
        # 时间过滤
        uploaded = datetime.fromisoformat(info.uploaded_at)
        if before and uploaded >= before:
            continue
        if after and uploaded <= after:
            continue
        
        files.append(info)
    
    # 按上传时间倒序排列 (最新的在前)
    files.sort(key=lambda x: x.uploaded_at, reverse=True)
    
    return files


# ============ API 端点 ============

@router.get("/files", response_model=FileListResponse)
async def list_files(
    status: Optional[str] = Query(
        default=None, 
        description="状态过滤 (available/expired)"
    ),
    before: Optional[str] = Query(
        default=None,
        description="只返回此时间之前上传的文件 (ISO 8601)"
    ),
    after: Optional[str] = Query(
        default=None,
        description="只返回此时间之后上传的文件 (ISO 8601)"
    ),
    limit: int = Query(default=100, ge=1, le=1000, description="返回数量限制"),
    offset: int = Query(default=0, ge=0, description="偏移量"),
):
    """
    列出已上传的临时文件
    
    返回上传目录中的所有文件信息，支持状态和时间过滤。
    """
    # 解析时间参数
    before_dt = None
    after_dt = None
    
    if before:
        try:
            before_dt = datetime.fromisoformat(before.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"无效的时间格式: {before}"
            )
    
    if after:
        try:
            after_dt = datetime.fromisoformat(after.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"无效的时间格式: {after}"
            )
    
    # 验证状态参数
    if status and status not in ("available", "expired"):
        raise HTTPException(
            status_code=400,
            detail=f"无效的状态: {status}，有效值为 'available' 或 'expired'"
        )
    
    # 获取文件列表
    all_files = _list_all_files(
        status_filter=status,
        before=before_dt,
        after=after_dt,
    )
    
    # 分页
    total_count = len(all_files)
    paginated_files = all_files[offset:offset + limit]
    
    # 计算总大小 (全部文件，不只是当前页)
    total_size_mb = round(sum(f.size_mb for f in all_files), 3)
    
    return FileListResponse(
        files=paginated_files,
        total_count=total_count,
        total_size_mb=total_size_mb,
        upload_dir=str(_get_upload_dir()),
    )


@router.get("/files/{file_id}", response_model=FileInfo)
async def get_file(file_id: str):
    """
    获取单个文件信息
    
    Args:
        file_id: 文件唯一标识
    """
    file_path = _find_file_by_id(file_id)
    
    if file_path is None:
        raise HTTPException(
            status_code=404,
            detail=f"文件不存在: {file_id}"
        )
    
    info = _get_file_info(file_path)
    if info is None:
        raise HTTPException(
            status_code=404,
            detail=f"无法获取文件信息: {file_id}"
        )
    
    return info


@router.delete("/files/{file_id}", response_model=FileDeleteResponse)
async def delete_file(file_id: str):
    """
    手动删除文件
    
    Args:
        file_id: 文件唯一标识
    """
    file_path = _find_file_by_id(file_id)
    
    if file_path is None:
        raise HTTPException(
            status_code=404,
            detail=f"文件不存在: {file_id}"
        )
    
    try:
        filename = file_path.name
        file_path.unlink()
        
        logger.info(f"已删除文件: {filename} (ID: {file_id})")
        
        return FileDeleteResponse(
            success=True,
            message=f"文件 '{filename}' 已删除",
            file_id=file_id,
        )
    except PermissionError:
        raise HTTPException(
            status_code=403,
            detail=f"无权删除文件: {file_id}"
        )
    except Exception as e:
        logger.error(f"删除文件失败 {file_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"删除文件失败: {str(e)}"
        )


@router.post("/files/cleanup", response_model=CleanupResponse)
async def cleanup_files(request: CleanupRequest = None):
    """
    清理过期文件
    
    支持多种清理条件:
    - 按时间: 清理指定时间之前的文件
    - 按年龄: 清理超过指定时长的文件
    - 按状态: 只清理已过期的文件
    
    使用 dry_run=true 可预览将要删除的文件，不实际执行删除。
    """
    if request is None:
        request = CleanupRequest()
    
    # 确定清理截止时间
    cutoff_time = None
    
    if request.before:
        try:
            cutoff_time = datetime.fromisoformat(
                request.before.replace('Z', '+00:00')
            )
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"无效的时间格式: {request.before}"
            )
    elif request.max_age_hours is not None:
        cutoff_time = datetime.now(timezone.utc) - timedelta(
            hours=request.max_age_hours
        )
    
    # 获取要清理的文件
    upload_dir = _get_upload_dir()
    files_to_delete = []
    total_size = 0
    
    for file_path in upload_dir.iterdir():
        if not file_path.is_file():
            continue
        
        # 跳过隐藏文件
        if file_path.name.startswith('.'):
            continue
        
        info = _get_file_info(file_path)
        if info is None:
            continue
        
        should_delete = False
        
        # 检查状态条件
        if request.status == "expired":
            if info.status == "expired":
                should_delete = True
        elif request.status == "all":
            should_delete = True
        elif cutoff_time:
            # 检查时间条件
            uploaded = datetime.fromisoformat(info.uploaded_at)
            if uploaded < cutoff_time:
                should_delete = True
        elif request.status is None and cutoff_time is None:
            # 默认：清理已过期文件
            if info.status == "expired":
                should_delete = True
        
        if should_delete:
            files_to_delete.append((file_path, info))
            total_size += info.size_mb
    
    # 执行删除
    deleted_count = 0
    deleted_files = []
    
    for file_path, info in files_to_delete:
        deleted_files.append(info.filename)
        
        if not request.dry_run:
            try:
                file_path.unlink()
                deleted_count += 1
                logger.info(f"清理文件: {info.filename}")
            except Exception as e:
                logger.warning(f"清理文件失败 {info.filename}: {e}")
        else:
            deleted_count += 1  # dry_run 模式下也计数
    
    # 生成消息
    if request.dry_run:
        message = f"预览模式: 将删除 {deleted_count} 个文件，释放 {round(total_size, 2)} MB"
    else:
        message = f"已清理 {deleted_count} 个文件，释放 {round(total_size, 2)} MB"
    
    if deleted_count == 0:
        message = "没有需要清理的文件"
    
    logger.info(message)
    
    return CleanupResponse(
        success=True,
        message=message,
        deleted_count=deleted_count,
        freed_mb=round(total_size, 3),
        deleted_files=deleted_files,
        dry_run=request.dry_run,
    )


@router.get("/files/stats", response_model=dict)
async def get_files_stats():
    """
    获取文件统计信息
    
    返回上传目录的总体统计，包括文件数量、大小、状态分布等。
    """
    all_files = _list_all_files()
    
    # 统计
    total_count = len(all_files)
    available_count = sum(1 for f in all_files if f.status == "available")
    expired_count = sum(1 for f in all_files if f.status == "expired")
    total_size_mb = round(sum(f.size_mb for f in all_files), 3)
    available_size_mb = round(
        sum(f.size_mb for f in all_files if f.status == "available"), 3
    )
    expired_size_mb = round(
        sum(f.size_mb for f in all_files if f.status == "expired"), 3
    )
    
    # 文件类型分布
    extensions = {}
    for f in all_files:
        ext = Path(f.filename).suffix.lower() or "(无扩展名)"
        if ext not in extensions:
            extensions[ext] = {"count": 0, "size_mb": 0}
        extensions[ext]["count"] += 1
        extensions[ext]["size_mb"] = round(
            extensions[ext]["size_mb"] + f.size_mb, 3
        )
    
    # 最早和最晚上传时间
    oldest = min((f.uploaded_at for f in all_files), default=None)
    newest = max((f.uploaded_at for f in all_files), default=None)
    
    return {
        "upload_dir": str(_get_upload_dir()),
        "total_count": total_count,
        "total_size_mb": total_size_mb,
        "by_status": {
            "available": {
                "count": available_count,
                "size_mb": available_size_mb,
            },
            "expired": {
                "count": expired_count,
                "size_mb": expired_size_mb,
            },
        },
        "by_extension": extensions,
        "oldest_file": oldest,
        "newest_file": newest,
        "default_expiry_hours": DEFAULT_EXPIRY_HOURS,
    }
