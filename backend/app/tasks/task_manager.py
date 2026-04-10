"""
In-memory background task manager using threading.
Replaces Celery for simplicity — tasks run in daemon threads
and results are stored in a thread-safe dict.
"""

import uuid
import threading
import traceback
from typing import Any, Callable, Dict, Optional
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class TaskInfo:
    token: str
    status: str = "pending"  # pending | running | completed | failed
    progress: float = 0.0
    result: Any = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class TaskManager:
    """Thread-safe in-memory task manager."""

    def __init__(self):
        self._tasks: Dict[str, TaskInfo] = {}
        self._lock = threading.Lock()

    def submit(self, fn: Callable, *args, **kwargs) -> str:
        """
        Submit a function to run in a background thread.
        Returns a task_token for polling.

        The function `fn` receives `task_token` and `task_manager` as first two args
        so it can report progress.
        """
        token = str(uuid.uuid4())
        task_info = TaskInfo(token=token)

        with self._lock:
            self._tasks[token] = task_info

        def _worker():
            with self._lock:
                self._tasks[token].status = "running"
            try:
                result = fn(token, self, *args, **kwargs)
                with self._lock:
                    self._tasks[token].status = "completed"
                    self._tasks[token].result = result
                    self._tasks[token].progress = 1.0
                    self._tasks[token].completed_at = datetime.utcnow()
            except Exception as e:
                with self._lock:
                    self._tasks[token].status = "failed"
                    self._tasks[token].error = f"{type(e).__name__}: {str(e)}"
                    self._tasks[token].completed_at = datetime.utcnow()
                traceback.print_exc()

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
        return token

    def update_progress(self, token: str, progress: float):
        """Called by the running task to report progress (0.0 → 1.0)."""
        with self._lock:
            if token in self._tasks:
                self._tasks[token].progress = min(1.0, max(0.0, progress))

    def get_status(self, token: str) -> Optional[TaskInfo]:
        with self._lock:
            return self._tasks.get(token)

    def cleanup_old(self, max_age_seconds: int = 3600):
        """Remove completed tasks older than max_age_seconds."""
        now = datetime.utcnow()
        with self._lock:
            to_remove = [
                t for t, info in self._tasks.items()
                if info.completed_at and (now - info.completed_at).total_seconds() > max_age_seconds
            ]
            for t in to_remove:
                del self._tasks[t]


# Singleton instance shared across the application
task_manager = TaskManager()
