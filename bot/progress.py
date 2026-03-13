"""
Progress Tracker for download tasks

Tracks download progress and determines when to send notifications.
Notifications are sent every 10% of progress.

Requirements: 6.6
"""

from typing import Dict


class ProgressTracker:
    """Tracks progress of download tasks and manages notification thresholds"""
    
    def __init__(self):
        """Initialize progress tracker"""
        # Store last notified progress for each task (in percentage)
        self._last_notified: Dict[str, int] = {}
        # Store current progress for each task (0.0 - 1.0)
        self._current_progress: Dict[str, float] = {}
    
    async def update_progress(self, task_id: str, progress: float) -> None:
        """
        Update progress for a task
        
        Args:
            task_id: ID of the download task
            progress: Progress value (0.0 - 1.0)
        """
        # Clamp progress to valid range
        progress = max(0.0, min(1.0, progress))
        self._current_progress[task_id] = progress
        
        # Initialize last notified if not present
        if task_id not in self._last_notified:
            self._last_notified[task_id] = 0
    
    async def should_notify(self, task_id: str, current_progress: float) -> bool:
        """
        Check if notification should be sent for current progress
        
        Notifications are sent every 10% of progress (10%, 20%, 30%, etc.)
        
        Args:
            task_id: ID of the download task
            current_progress: Current progress value (0.0 - 1.0)
        
        Returns:
            True if notification should be sent, False otherwise
        """
        # Clamp progress to valid range
        current_progress = max(0.0, min(1.0, current_progress))
        
        # Convert to percentage
        current_percent = int(current_progress * 100)
        
        # Get last notified percentage (default to 0)
        last_notified_percent = self._last_notified.get(task_id, 0)
        
        # Calculate current threshold (multiple of 10)
        current_threshold = (current_percent // 10) * 10
        
        # Should notify if we've crossed a 10% threshold
        if current_threshold > last_notified_percent and current_threshold > 0:
            # Update last notified
            self._last_notified[task_id] = current_threshold
            return True
        
        return False
    
    def get_progress(self, task_id: str) -> float:
        """
        Get current progress for a task
        
        Args:
            task_id: ID of the download task
        
        Returns:
            Progress value (0.0 - 1.0), or 0.0 if task not found
        """
        return self._current_progress.get(task_id, 0.0)
    
    def clear_task(self, task_id: str) -> None:
        """
        Clear progress tracking for a task
        
        Args:
            task_id: ID of the download task
        """
        self._last_notified.pop(task_id, None)
        self._current_progress.pop(task_id, None)
