"""
tasks.py - 异步任务管理 API
=============================

端点:
- GET /tasks - 列出所有任务
- GET /tasks/{task_id} - 获取任务详情
- DELETE /tasks/{task_id} - 取消/删除任务
"""

import uuid
import logging
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from threading import Lock

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


# ============ 任务状态和管理器 ============

class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"        # 等待处理
    PROCESSING = "processing"  # 处理中
    COMPLETED = "completed"    # 已完成
    FAILED = "failed"          # 失败
    CANCELLED = "cancelled"    # 已取消


@dataclass
class Task:
    """任务对象"""
    task_id: str
    status: TaskStatus
    engine: str
    model: Optional[str]
    audio_path: str
    callback_url: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    progress: float = 0.0
    progress_current: int = 0        # 当前处理段数
    progress_total: int = 0          # 总段数
    progress_message: str = ""       # 进度信息
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "engine": self.engine,
            "model": self.model,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "progress": self.progress,
            "progress_current": self.progress_current,
            "progress_total": self.progress_total,
            "progress_message": self.progress_message,
            "result": self.result,
            "error": self.error,
        }


class TaskManager:
    """
    任务管理器 (内存存储)
    
    注意: 生产环境应使用 Redis 或数据库存储
    """
    
    def __init__(self, max_tasks: int = 1000):
        self._tasks: Dict[str, Task] = {}
        self._lock = Lock()
        self._max_tasks = max_tasks
    
    def create_task(
        self,
        engine: str,
        model: Optional[str],
        audio_path: str,
        callback_url: Optional[str] = None,
    ) -> str:
        """创建新任务"""
        task_id = str(uuid.uuid4())
        
        with self._lock:
            # 清理旧任务 (FIFO)
            if len(self._tasks) >= self._max_tasks:
                oldest_id = min(self._tasks.keys(), key=lambda k: self._tasks[k].created_at)
                del self._tasks[oldest_id]
            
            self._tasks[task_id] = Task(
                task_id=task_id,
                status=TaskStatus.PENDING,
                engine=engine,
                model=model,
                audio_path=audio_path,
                callback_url=callback_url,
            )
        
        return task_id
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        return self._tasks.get(task_id)
    
    def update_task(
        self,
        task_id: str,
        status: Optional[TaskStatus] = None,
        progress: Optional[float] = None,
        progress_current: Optional[int] = None,
        progress_total: Optional[int] = None,
        progress_message: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> bool:
        """更新任务"""
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False
            
            if status is not None:
                task.status = status
            if progress is not None:
                task.progress = progress
            if progress_current is not None:
                task.progress_current = progress_current
            if progress_total is not None:
                task.progress_total = progress_total
            if progress_message is not None:
                task.progress_message = progress_message
            if result is not None:
                task.result = result
            if error is not None:
                task.error = error
            
            task.updated_at = datetime.now()
            return True
    
    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        with self._lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
                return True
            return False
    
    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Task]:
        """列出任务"""
        tasks = list(self._tasks.values())
        
        # 过滤状态
        if status:
            tasks = [t for t in tasks if t.status == status]
        
        # 按创建时间倒序
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        
        # 分页
        return tasks[offset:offset + limit]
    
    def count_tasks(self, status: Optional[TaskStatus] = None) -> int:
        """统计任务数量"""
        if status:
            return sum(1 for t in self._tasks.values() if t.status == status)
        return len(self._tasks)


# 全局任务管理器实例
task_manager = TaskManager()


# ============ Pydantic 响应模型 ============

class TaskInfo(BaseModel):
    """任务简要信息"""
    task_id: str
    status: str
    engine: str
    created_at: str
    progress: float


class TaskDetailResponse(BaseModel):
    """任务详情响应"""
    task_id: str
    status: str
    engine: str
    model: Optional[str]
    created_at: str
    updated_at: str
    progress: float
    progress_current: int = 0        # 当前处理段数
    progress_total: int = 0          # 总段数
    progress_message: str = ""       # 进度信息 (如 "识别第 3/10 段")
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class TaskListResponse(BaseModel):
    """任务列表响应"""
    tasks: List[TaskInfo]
    total: int


class DeleteTaskResponse(BaseModel):
    """删除任务响应"""
    task_id: str
    message: str


# ============ API 端点 ============

@router.get("/tasks", response_model=TaskListResponse)
async def list_tasks(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    """
    列出所有任务
    
    可通过 status 参数过滤: pending, processing, completed, failed, cancelled
    """
    # 解析状态
    status_enum = None
    if status:
        try:
            status_enum = TaskStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"无效的状态: {status}。有效值: {[s.value for s in TaskStatus]}"
            )
    
    # 获取任务列表
    tasks = task_manager.list_tasks(status=status_enum, limit=limit, offset=offset)
    total = task_manager.count_tasks(status=status_enum)
    
    return TaskListResponse(
        tasks=[
            TaskInfo(
                task_id=t.task_id,
                status=t.status.value,
                engine=t.engine,
                created_at=t.created_at.isoformat(),
                progress=t.progress,
            )
            for t in tasks
        ],
        total=total,
    )


@router.get("/tasks/{task_id}", response_model=TaskDetailResponse)
async def get_task(task_id: str):
    """
    获取任务详情
    
    返回任务的完整信息，包括识别结果 (如果已完成)。
    
    进度信息:
    - progress: 0.0 ~ 1.0 的进度比例
    - progress_current: 当前已处理段数
    - progress_total: 总段数
    - progress_message: 可读的进度信息 (如 "识别第 3/10 段")
    """
    task = task_manager.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail=f"任务 '{task_id}' 不存在")
    
    return TaskDetailResponse(
        task_id=task.task_id,
        status=task.status.value,
        engine=task.engine,
        model=task.model,
        created_at=task.created_at.isoformat(),
        updated_at=task.updated_at.isoformat(),
        progress=task.progress,
        progress_current=task.progress_current,
        progress_total=task.progress_total,
        progress_message=task.progress_message,
        result=task.result,
        error=task.error,
    )


@router.delete("/tasks/{task_id}", response_model=DeleteTaskResponse)
async def delete_task(task_id: str):
    """
    删除任务
    
    如果任务正在处理中，将尝试取消。
    """
    task = task_manager.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail=f"任务 '{task_id}' 不存在")
    
    # 如果正在处理，标记为取消
    if task.status == TaskStatus.PROCESSING:
        task_manager.update_task(task_id, status=TaskStatus.CANCELLED)
        return DeleteTaskResponse(
            task_id=task_id,
            message="任务已标记为取消",
        )
    
    # 直接删除
    task_manager.delete_task(task_id)
    return DeleteTaskResponse(
        task_id=task_id,
        message="任务已删除",
    )
