"""
Resource Monitor

Monitors system resource usage (memory, CPU) and implements throttling
when resources are constrained.

Requirements: 15.1, 15.3, 15.4, 15.5
"""

import psutil
import asyncio
import logging
from typing import Optional


logger = logging.getLogger(__name__)


class ResourceMonitor:
    """Monitors system resources and manages throttling"""
    
    def __init__(self, memory_threshold: float = 0.8, check_interval: int = 30):
        """
        Initialize resource monitor
        
        Args:
            memory_threshold: Memory usage threshold (0.0-1.0) for throttling
            check_interval: Interval in seconds between checks
            
        Requirements: 15.1, 15.5
        """
        self.memory_threshold = memory_threshold
        self.check_interval = check_interval
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._throttled = False
        self._download_manager = None
    
    def set_download_manager(self, download_manager) -> None:
        """Set download manager for throttling control"""
        self._download_manager = download_manager
    
    async def start_monitoring(self) -> None:
        """
        Start resource monitoring
        
        Requirements: 15.1
        """
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Resource monitoring started")
    
    async def stop_monitoring(self) -> None:
        """Stop resource monitoring"""
        self._monitoring = False
        
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None
        
        logger.info("Resource monitoring stopped")
    
    async def _monitor_loop(self) -> None:
        """Main monitoring loop"""
        while self._monitoring:
            try:
                await self._check_resources()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in resource monitoring: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _check_resources(self) -> None:
        """
        Check system resources and apply throttling if needed
        
        Requirements: 15.5
        """
        # Get memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent / 100.0
        
        # Get process memory
        process = psutil.Process()
        process_memory_mb = process.memory_info().rss / (1024 * 1024)
        
        logger.debug(
            f"Resource usage: System memory={memory_percent:.1%}, "
            f"Process memory={process_memory_mb:.1f}MB"
        )
        
        # Check if we need to throttle
        if memory_percent > self.memory_threshold:
            if not self._throttled:
                logger.warning(
                    f"Memory usage high ({memory_percent:.1%}), enabling throttling"
                )
                self._throttled = True
                
                # Pause new downloads if download manager is available
                if self._download_manager:
                    # Note: This would require adding a pause_new_downloads method
                    # to DownloadManager
                    pass
        else:
            if self._throttled:
                logger.info(
                    f"Memory usage normal ({memory_percent:.1%}), disabling throttling"
                )
                self._throttled = False
                
                # Resume downloads if download manager is available
                if self._download_manager:
                    # Note: This would require adding a resume_new_downloads method
                    # to DownloadManager
                    pass
    
    def get_memory_usage(self) -> dict:
        """
        Get current memory usage statistics
        
        Returns:
            Dictionary with memory usage info:
            {
                "system_percent": float,
                "system_available_mb": float,
                "process_mb": float,
                "throttled": bool
            }
            
        Requirements: 15.1
        """
        memory = psutil.virtual_memory()
        process = psutil.Process()
        
        return {
            "system_percent": memory.percent / 100.0,
            "system_available_mb": memory.available / (1024 * 1024),
            "process_mb": process.memory_info().rss / (1024 * 1024),
            "throttled": self._throttled
        }
    
    def is_throttled(self) -> bool:
        """
        Check if system is currently throttled
        
        Returns:
            True if throttled, False otherwise
            
        Requirements: 15.5
        """
        return self._throttled
    
    async def wait_for_resources(self, timeout: int = 300) -> bool:
        """
        Wait for resources to become available
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if resources available, False if timeout
            
        Requirements: 15.5
        """
        start_time = asyncio.get_event_loop().time()
        
        while self._throttled:
            # Check if timeout exceeded
            if asyncio.get_event_loop().time() - start_time > timeout:
                return False
            
            # Wait a bit and check again
            await asyncio.sleep(5)
        
        return True
