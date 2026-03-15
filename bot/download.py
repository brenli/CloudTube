"""
Download service for managing video downloads

Provides metadata extraction and download task management using yt-dlp.
Handles both individual videos and playlists.

Requirements: 3.1, 3.2, 4.1, 4.2, 3.3, 3.5, 10.1, 10.2, 15.2, 3.3, 4.3, 5.1, 5.2, 5.3, 5.4, 7.1, 7.2, 7.5, 7.6, 8.1, 8.3
"""

import yt_dlp
import asyncio
import os
import tempfile
import uuid
import logging
from dataclasses import dataclass
from typing import Optional, Callable
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class VideoMetadata:
    """Video metadata extracted from YouTube"""
    video_id: str
    title: str
    duration: int  # seconds
    available_qualities: list[str]
    estimated_sizes: dict[str, int]  # quality -> size in bytes


class DownloadService:
    """Service for managing video downloads"""
    
    def __init__(self):
        """Initialize download service"""
        # Common yt-dlp options for metadata extraction
        self._ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            # Add headers to bypass YouTube restrictions
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'referer': 'https://www.youtube.com/',
        }
    
    async def get_video_metadata(self, url: str) -> VideoMetadata:
        """
        Extract metadata for a single video
        
        Args:
            url: YouTube video URL
            
        Returns:
            VideoMetadata with video information
            
        Raises:
            ValueError: If URL is invalid or video is unavailable
            
        Requirements: 3.1, 3.2
        """
        try:
            # Run yt-dlp in thread pool to avoid blocking event loop
            def _extract_metadata():
                with yt_dlp.YoutubeDL(self._ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    
                    if info is None:
                        raise ValueError(f"Could not extract video information from URL: {url}")
                    
                    # Extract video ID
                    video_id = info.get('id', '')
                    if not video_id:
                        raise ValueError(f"Could not extract video ID from URL: {url}")
                    
                    # Extract title
                    title = info.get('title', 'Unknown')
                    
                    # Extract duration
                    duration = info.get('duration', 0)
                    
                    # Extract available formats and qualities
                    formats = info.get('formats', [])
                    
                    # Build quality map with estimated sizes
                    quality_map = {}
                    available_qualities = []
                    
                    # Define quality priorities (best to worst)
                    quality_priorities = ['best', '1080p', '720p', '480p', '360p']
                    
                    # Group formats by quality
                    for fmt in formats:
                        # Skip audio-only formats
                        if fmt.get('vcodec') == 'none':
                            continue
                        
                        height = fmt.get('height')
                        filesize = fmt.get('filesize') or fmt.get('filesize_approx', 0)
                        
                        if height:
                            quality = f"{height}p"
                            
                            # Keep the largest filesize for each quality
                            if quality not in quality_map or filesize > quality_map[quality]:
                                quality_map[quality] = filesize
                    
                    # Add 'best' quality (use the highest resolution available)
                    if quality_map:
                        best_size = max(quality_map.values())
                        quality_map['best'] = best_size
                    
                    # Build available qualities list in priority order
                    for quality in quality_priorities:
                        if quality == 'best' or quality in quality_map:
                            available_qualities.append(quality)
                    
                    # If no qualities found, add a default
                    if not available_qualities:
                        available_qualities = ['best']
                        quality_map['best'] = info.get('filesize', 0) or info.get('filesize_approx', 0)
                    
                    return VideoMetadata(
                        video_id=video_id,
                        title=title,
                        duration=duration,
                        available_qualities=available_qualities,
                        estimated_sizes=quality_map
                    )
            
            # Run in thread pool
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, _extract_metadata)
                
        except yt_dlp.utils.DownloadError as e:
            raise ValueError(f"Failed to extract video metadata: {str(e)}")
        except Exception as e:
            raise ValueError(f"Unexpected error extracting video metadata: {str(e)}")
    
    async def get_playlist_metadata(self, url: str) -> list[VideoMetadata]:
        """
        Extract metadata for all videos in a playlist
        
        Args:
            url: YouTube playlist URL
            
        Returns:
            List of VideoMetadata for each video in the playlist
            
        Raises:
            ValueError: If URL is invalid or playlist is unavailable
            
        Requirements: 4.1, 4.2
        """
        try:
            # Options for playlist extraction
            playlist_opts = {
                **self._ydl_opts,
                'extract_flat': 'in_playlist',  # Extract basic info for playlist items
            }
            
            # Run yt-dlp in thread pool to avoid blocking
            def _extract_playlist():
                with yt_dlp.YoutubeDL(playlist_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    
                    if info is None:
                        raise ValueError(f"Could not extract playlist information from URL: {url}")
                    
                    # Check if this is a playlist
                    if 'entries' not in info:
                        raise ValueError(f"URL does not appear to be a playlist: {url}")
                    
                    entries = info.get('entries', [])
                    
                    if not entries:
                        raise ValueError(f"Playlist is empty: {url}")
                    
                    return entries
            
            # Run in thread pool
            loop = asyncio.get_event_loop()
            entries = await loop.run_in_executor(None, _extract_playlist)
            
            # Extract metadata for each video
            metadata_list = []
            
            for entry in entries:
                # Skip unavailable videos
                if entry is None:
                    continue
                
                # Get video URL
                video_id = entry.get('id')
                if not video_id:
                    continue
                
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                
                try:
                    # Extract full metadata for each video
                    video_metadata = await self.get_video_metadata(video_url)
                    metadata_list.append(video_metadata)
                except ValueError:
                    # Skip videos that fail to extract
                    continue
            
            if not metadata_list:
                raise ValueError(f"No valid videos found in playlist: {url}")
            
            return metadata_list
                
        except yt_dlp.utils.DownloadError as e:
            raise ValueError(f"Failed to extract playlist metadata: {str(e)}")
        except ValueError:
            # Re-raise ValueError as-is
            raise
        except Exception as e:
            raise ValueError(f"Unexpected error extracting playlist metadata: {str(e)}")



class TaskExecutor:
    """
    Task executor for downloading videos
    
    Handles video download execution with retry logic, streaming,
    and integration with WebDAV storage.
    
    Requirements: 3.3, 3.5, 10.1, 10.2, 15.2
    """
    
    def __init__(self, webdav_service, temp_dir: Optional[str] = None):
        """
        Initialize task executor
        
        Args:
            webdav_service: WebDAV service instance for file uploads
            temp_dir: Temporary directory for downloads (uses system temp if None)
        """
        self.webdav_service = webdav_service
        self.temp_dir = temp_dir or tempfile.gettempdir()
        
        # Ensure temp directory exists
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Retry configuration
        self.max_retries = 3
        self.base_delay = 1.0  # seconds
    
    async def execute_download(
        self,
        task,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> str:
        """
        Execute download task with retry logic
        
        Args:
            task: DownloadTask to execute
            progress_callback: Optional callback for progress updates (0.0 to 1.0)
            
        Returns:
            Path to downloaded file in temporary storage
            
        Raises:
            Exception: If download fails after all retries
            
        Requirements: 3.3, 10.1, 10.2
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Attempt {attempt + 1}/{self.max_retries} for task {task.task_id}")
                
                # Download video
                local_path = await self.download_video(
                    url=task.url,
                    quality=task.quality,
                    output_path=self._get_temp_path(task.task_id),
                    progress_callback=progress_callback
                )
                
                logger.info(f"Download successful on attempt {attempt + 1}")
                return local_path
                
            except Exception as e:
                last_error = e
                logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
                
                # If this is not the last attempt, wait with exponential backoff
                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt)
                    logger.info(f"Waiting {delay}s before retry...")
                    await asyncio.sleep(delay)
                    continue
        
        # All retries exhausted
        error_msg = f"Download failed after {self.max_retries} attempts: {str(last_error)}"
        logger.error(error_msg)
        raise Exception(error_msg)
    
    async def download_video(
        self,
        url: str,
        quality: str,
        output_path: str,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> str:
        """
        Download video using yt-dlp with streaming
        
        Args:
            url: YouTube video URL
            quality: Quality to download (best, 1080p, 720p, 480p, 360p)
            output_path: Output file path (without extension)
            progress_callback: Optional callback for progress updates
            
        Returns:
            Path to downloaded video file
            
        Raises:
            Exception: If download fails
            
        Requirements: 3.5, 15.2
        """
        # Store progress updates to process asynchronously
        progress_updates = []
        
        # Progress hook for yt-dlp (must be synchronous)
        def progress_hook(d):
            if progress_callback and d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                downloaded = d.get('downloaded_bytes', 0)
                
                if total > 0:
                    progress = downloaded / total
                    # Schedule async callback
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            asyncio.create_task(progress_callback(progress))
                    except Exception:
                        # If we can't schedule, just skip this progress update
                        pass
        
        # Configure yt-dlp options
        ydl_opts = {
            'format': self._get_format_string(quality),
            'outtmpl': f'{output_path}.%(ext)s',
            'progress_hooks': [progress_hook],
            'quiet': True,
            'no_warnings': True,
            # Force MP4 format
            'merge_output_format': 'mp4',
            # Use streaming to minimize memory usage
            'http_chunk_size': 10485760,  # 10MB chunks
            # Add headers to bypass YouTube restrictions
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'referer': 'https://www.youtube.com/',
            # Additional options to help with YouTube restrictions
            'nocheckcertificate': True,
            'prefer_insecure': False,
            'age_limit': None,
        }
        
        # Download video in a separate thread to avoid blocking event loop
        def _download_sync():
            logger.info(f"Starting yt-dlp download for URL: {url}")
            logger.info(f"Quality: {quality}, Output: {output_path}")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                if info is None:
                    raise Exception(f"Failed to download video from URL: {url}")
                
                logger.info("yt-dlp extraction completed")
                
                # Get the actual filename
                filename = ydl.prepare_filename(info)
                logger.info(f"Prepared filename: {filename}")
                
                # Ensure it's MP4
                if not filename.endswith('.mp4'):
                    # yt-dlp should have merged to mp4, but check
                    base = os.path.splitext(filename)[0]
                    mp4_file = f"{base}.mp4"
                    if os.path.exists(mp4_file):
                        filename = mp4_file
                        logger.info(f"Found MP4 file: {filename}")
                
                if not os.path.exists(filename):
                    raise Exception(f"Downloaded file not found: {filename}")
                
                file_size = os.path.getsize(filename)
                logger.info(f"Downloaded file size: {file_size} bytes")
                
                return filename
        
        # Run in thread pool to avoid blocking
        logger.info("Submitting download to thread pool")
        loop = asyncio.get_event_loop()
        filename = await loop.run_in_executor(None, _download_sync)
        logger.info(f"Thread pool execution completed: {filename}")
        
        return filename
    
    def _get_format_string(self, quality: str) -> str:
        """
        Get yt-dlp format string for quality
        
        Args:
            quality: Quality string (best, 1080p, 720p, 480p, 360p)
            
        Returns:
            yt-dlp format string
        """
        if quality == 'best':
            return 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        
        # Extract height from quality string (e.g., "1080p" -> 1080)
        height = quality.rstrip('p')
        
        # Format: video with specified height + audio, fallback to best
        return f'bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/best[height<={height}][ext=mp4]/best'
    
    def _get_temp_path(self, task_id: str) -> str:
        """
        Get temporary file path for task
        
        Args:
            task_id: Task ID
            
        Returns:
            Path to temporary file (without extension)
        """
        return os.path.join(self.temp_dir, f"download_{task_id}")
    
    async def cleanup_temp_files(self, task_id: str) -> None:
        """
        Clean up temporary files for a task
        
        Args:
            task_id: Task ID to clean up
            
        Requirements: 7.3
        """
        temp_path = self._get_temp_path(task_id)
        
        # Try to remove files with common extensions
        for ext in ['.mp4', '.webm', '.mkv', '.part', '.ytdl', '.temp']:
            file_path = f"{temp_path}{ext}"
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception:
                # Ignore errors during cleanup
                pass
        
        # Also try to remove the base path if it exists
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception:
            pass



class TaskQueue:
    """
    Task queue for managing download tasks
    
    Manages a queue of download tasks with limited concurrent execution.
    Uses asyncio.Queue for async task processing.
    
    Requirements: 5.1, 5.3, 5.4
    """
    
    def __init__(self, max_concurrent: int = 2):
        """
        Initialize task queue
        
        Args:
            max_concurrent: Maximum number of concurrent downloads (default: 2)
        """
        self.max_concurrent = max_concurrent
        self._queue: asyncio.Queue = asyncio.Queue()
        self._workers: list[asyncio.Task] = []
        self._active_tasks: dict[str, asyncio.Task] = {}
        self._running = False
        self._task_executor: Optional[TaskExecutor] = None
        self._database = None
        self._progress_tracker = None
        self._notification_service = None
    
    def set_dependencies(self, task_executor, database, progress_tracker, notification_service):
        """
        Set dependencies for task execution
        
        Args:
            task_executor: TaskExecutor instance
            database: Database instance
            progress_tracker: ProgressTracker instance
            notification_service: NotificationService instance
        """
        self._task_executor = task_executor
        self._database = database
        self._progress_tracker = progress_tracker
        self._notification_service = notification_service
    
    async def enqueue(self, task) -> None:
        """
        Add a task to the queue
        
        Args:
            task: DownloadTask to enqueue
            
        Requirements: 5.1
        """
        await self._queue.put(task)
    
    async def start_processing(self) -> None:
        """
        Start processing tasks from the queue
        
        Creates worker tasks up to max_concurrent limit.
        
        Requirements: 5.3, 5.4
        """
        if self._running:
            return
        
        self._running = True
        
        # Create worker tasks
        for i in range(self.max_concurrent):
            worker = asyncio.create_task(self._worker(i))
            self._workers.append(worker)
    
    async def stop_processing(self) -> None:
        """
        Stop processing tasks from the queue
        
        Waits for active tasks to complete and cancels workers.
        """
        self._running = False
        
        # Cancel all workers
        for worker in self._workers:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self._workers, return_exceptions=True)
        
        self._workers.clear()
    
    async def _worker(self, worker_id: int) -> None:
        """
        Worker coroutine that processes tasks from the queue
        
        Args:
            worker_id: ID of this worker
        """
        while self._running:
            try:
                # Get task from queue with timeout
                try:
                    task = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                
                # Process the task
                await self._process_task(task)
                
                # Mark task as done
                self._queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                # Log error but continue processing
                logger.error(f"Worker {worker_id} error: {e}", exc_info=True)
    
    async def _process_task(self, task) -> None:
        """
        Process a single download task
        
        Args:
            task: DownloadTask to process
        """
        from bot.database import TaskStatus
        
        try:
            # Update task status to downloading
            task.status = TaskStatus.DOWNLOADING
            task.updated_at = datetime.now(timezone.utc)
            await self._database.update_task(task)
            
            # Send start notification if enabled
            if task.notification_settings.notify_start and self._notification_service:
                await self._notification_service.notify_download_start(task)
            
            # Progress callback
            async def progress_callback(progress: float):
                # Update progress in tracker
                await self._progress_tracker.update_progress(task.task_id, progress)
                
                # Update task progress
                task.progress = progress
                await self._database.update_task(task)
                
                # Check if we should notify
                if task.notification_settings.notify_progress and self._notification_service:
                    if await self._progress_tracker.should_notify(task.task_id, progress):
                        await self._notification_service.notify_download_progress(task, progress)
            
            # Execute download
            logger.info(f"Starting download for task {task.task_id}")
            local_path = await self._task_executor.execute_download(task, progress_callback)
            logger.info(f"Download completed. Local path: {local_path}")
            logger.info(f"File exists: {os.path.exists(local_path)}")
            if os.path.exists(local_path):
                logger.info(f"File size: {os.path.getsize(local_path)} bytes")
            
            # Determine remote path based on playlist membership
            if task.playlist_id and task.playlist_name:
                # Part of a playlist - organize in playlist folder
                remote_path = f"{task.playlist_name}/{os.path.basename(local_path)}"
            else:
                # Single video - save in "Single Videos" folder
                remote_path = f"Single Videos/{os.path.basename(local_path)}"
            
            logger.info(f"Remote path: {remote_path}")
            logger.info("Starting WebDAV upload...")
            
            # Upload to WebDAV
            await self._task_executor.webdav_service.upload_file(local_path, remote_path)
            
            logger.info("WebDAV upload completed successfully")
            
            # Update task as completed
            task.status = TaskStatus.COMPLETED
            task.progress = 1.0
            task.remote_path = remote_path
            task.updated_at = datetime.now(timezone.utc)
            await self._database.update_task(task)
            
            # Send completion notification if enabled
            if task.notification_settings.notify_completion and self._notification_service:
                await self._notification_service.notify_download_complete(task, remote_path)
            
            # Cleanup temp files
            await self._task_executor.cleanup_temp_files(task.task_id)
            
            # Clear progress tracking
            self._progress_tracker.clear_task(task.task_id)
            
        except Exception as e:
            # Update task as failed
            logger.error(f"Task {task.task_id} failed with error: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.updated_at = datetime.now(timezone.utc)
            await self._database.update_task(task)
            
            # Send error notification if enabled
            if task.notification_settings.notify_errors and self._notification_service:
                await self._notification_service.notify_download_error(task, str(e))
            
            # Cleanup temp files
            await self._task_executor.cleanup_temp_files(task.task_id)
            
            # Clear progress tracking
            self._progress_tracker.clear_task(task.task_id)


class DownloadManager:
    """
    Download manager for managing download tasks
    
    Provides high-level interface for creating, managing, and querying download tasks.
    Integrates TaskQueue, Database, and other services.
    
    Requirements: 3.3, 4.3, 7.1, 7.2, 7.5, 7.6, 8.1, 8.3, 4.4, 4.5, 4.6, 4.7, 7.8, 11.1
    """
    
    def __init__(self, database, task_executor, progress_tracker, notification_service, max_concurrent: int = 2):
        """
        Initialize download manager
        
        Args:
            database: Database instance
            task_executor: TaskExecutor instance
            progress_tracker: ProgressTracker instance
            notification_service: NotificationService instance
            max_concurrent: Maximum concurrent downloads (default: 2)
        """
        self._database = database
        self._task_executor = task_executor
        self._progress_tracker = progress_tracker
        self._notification_service = notification_service
        
        # Create task queue
        self._task_queue = TaskQueue(max_concurrent=max_concurrent)
        self._task_queue.set_dependencies(
            task_executor=task_executor,
            database=database,
            progress_tracker=progress_tracker,
            notification_service=notification_service
        )
        
        # Download service for metadata extraction
        self._download_service = DownloadService()
        
        # Track playlist tasks
        self._playlist_tasks: dict[str, list[str]] = {}  # playlist_id -> [task_ids]
    
    async def start(self) -> None:
        """Start the download manager"""
        await self._task_queue.start_processing()
    
    async def stop(self) -> None:
        """Stop the download manager"""
        await self._task_queue.stop_processing()
    
    async def create_download_task(
        self,
        url: str,
        quality: str,
        notification_settings
    ):
        """
        Create a new download task
        
        Args:
            url: YouTube video URL
            quality: Video quality to download
            notification_settings: NotificationSettings for this task
            
        Returns:
            Created DownloadTask
            
        Raises:
            ValueError: If URL is invalid or video is unavailable
            
        Requirements: 3.3
        """
        from bot.database import DownloadTask, TaskStatus
        
        # Extract video metadata
        metadata = await self._download_service.get_video_metadata(url)
        
        # Create task
        task = DownloadTask(
            task_id=str(uuid.uuid4()),
            url=url,
            video_id=metadata.video_id,
            title=metadata.title,
            quality=quality,
            status=TaskStatus.PENDING,
            progress=0.0,
            notification_settings=notification_settings,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Save to database
        await self._database.save_task(task)
        
        # Enqueue for processing
        await self._task_queue.enqueue(task)
        
        return task
    
    async def get_active_tasks(self) -> list:
        """
        Get all active download tasks
        
        Returns tasks with status "downloading" or "paused"
        
        Returns:
            List of active DownloadTask objects
            
        Requirements: 7.1
        """
        from bot.database import TaskStatus
        
        # Get downloading tasks
        downloading = await self._database.get_tasks_by_status(TaskStatus.DOWNLOADING)
        
        # Get paused tasks
        paused = await self._database.get_tasks_by_status(TaskStatus.PAUSED)
        
        # Combine and return
        return downloading + paused
    
    async def get_task_by_id(self, task_id: str):
        """
        Get a task by its ID
        
        Args:
            task_id: Task ID to retrieve
            
        Returns:
            DownloadTask or None if not found
            
        Requirements: 7.1
        """
        return await self._database.get_task(task_id)
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a download task
        
        Args:
            task_id: Task ID to cancel
            
        Returns:
            True if task was cancelled, False if not found or already completed
            
        Requirements: 7.2
        """
        from bot.database import TaskStatus
        
        # Get task
        task = await self._database.get_task(task_id)
        
        if task is None:
            return False
        
        # Can only cancel pending, downloading, or paused tasks
        if task.status not in [TaskStatus.PENDING, TaskStatus.DOWNLOADING, TaskStatus.PAUSED]:
            return False
        
        # Update status to cancelled
        task.status = TaskStatus.CANCELLED
        task.updated_at = datetime.now(timezone.utc)
        await self._database.update_task(task)
        
        # Cleanup temp files
        await self._task_executor.cleanup_temp_files(task_id)
        
        # Clear progress tracking
        self._progress_tracker.clear_task(task_id)
        
        return True
    
    async def pause_task(self, task_id: str) -> bool:
        """
        Pause a download task
        
        Args:
            task_id: Task ID to pause
            
        Returns:
            True if task was paused, False if not found or not downloading
            
        Requirements: 7.5
        """
        from bot.database import TaskStatus
        
        # Get task
        task = await self._database.get_task(task_id)
        
        if task is None:
            return False
        
        # Can only pause downloading tasks
        if task.status != TaskStatus.DOWNLOADING:
            return False
        
        # Update status to paused
        task.status = TaskStatus.PAUSED
        task.updated_at = datetime.now(timezone.utc)
        await self._database.update_task(task)
        
        return True
    
    async def resume_task(self, task_id: str) -> bool:
        """
        Resume a paused download task
        
        Args:
            task_id: Task ID to resume
            
        Returns:
            True if task was resumed, False if not found or not paused
            
        Requirements: 7.6
        """
        from bot.database import TaskStatus
        
        # Get task
        task = await self._database.get_task(task_id)
        
        if task is None:
            return False
        
        # Can only resume paused or interrupted tasks
        if task.status not in [TaskStatus.PAUSED, TaskStatus.INTERRUPTED]:
            return False
        
        # Update status to pending and re-enqueue
        task.status = TaskStatus.PENDING
        task.updated_at = datetime.now(timezone.utc)
        await self._database.update_task(task)
        
        # Re-enqueue for processing
        await self._task_queue.enqueue(task)
        
        return True
    
    async def get_history(self, status_filter: Optional[str] = None) -> list:
        """
        Get download history
        
        Args:
            status_filter: Optional status to filter by (e.g., "completed", "failed")
            
        Returns:
            List of DownloadTask objects
            
        Requirements: 8.1, 8.3
        """
        from bot.database import TaskStatus
        
        if status_filter:
            # Filter by status
            try:
                status = TaskStatus(status_filter)
                return await self._database.get_tasks_by_status(status)
            except ValueError:
                # Invalid status, return empty list
                return []
        else:
            # Return all tasks
            return await self._database.get_all_tasks()
    
    async def check_storage_space(self, estimated_size: int) -> dict:
        """
        Check if there's enough storage space for download
        
        Args:
            estimated_size: Estimated file size in bytes
            
        Returns:
            Dictionary with check results:
            {
                "has_space": bool,
                "free_space": int,
                "estimated_size": int,
                "warning": str (optional)
            }
            
        Requirements: 9.1, 9.2, 9.3
        """
        try:
            storage_info = await self._task_executor.webdav_service.get_storage_info()
            
            has_space = storage_info.free_space >= estimated_size
            
            result = {
                "has_space": has_space,
                "free_space": storage_info.free_space,
                "estimated_size": estimated_size
            }
            
            if not has_space:
                free_gb = storage_info.free_space / (1024**3)
                needed_gb = estimated_size / (1024**3)
                result["warning"] = (
                    f"⚠️ Недостаточно места в хранилище!\n"
                    f"Доступно: {free_gb:.2f} GB\n"
                    f"Требуется: {needed_gb:.2f} GB\n\n"
                    f"Выберите более низкое качество или освободите место"
                )
            
            return result
            
        except Exception as e:
            # If we can't check storage, assume we have space
            return {
                "has_space": True,
                "free_space": 0,
                "estimated_size": estimated_size,
                "warning": f"Не удалось проверить место в хранилище: {str(e)}"
            }
    
    async def create_playlist_tasks(
        self,
        url: str,
        quality: str,
        notification_settings,
        playlist_name: Optional[str] = None
    ) -> tuple[str, list]:
        """
        Create download tasks for all videos in a playlist
        
        Args:
            url: YouTube playlist URL
            quality: Video quality to download
            notification_settings: NotificationSettings for tasks
            playlist_name: Optional custom playlist name (extracted if None)
            
        Returns:
            Tuple of (playlist_id, list of created DownloadTask objects)
            
        Raises:
            ValueError: If URL is invalid or playlist is unavailable
            
        Requirements: 4.3
        """
        from bot.database import DownloadTask, TaskStatus
        
        # Extract playlist metadata
        videos_metadata = await self._download_service.get_playlist_metadata(url)
        
        # Generate playlist ID
        playlist_id = str(uuid.uuid4())
        
        # Create tasks for each video
        tasks = []
        task_ids = []
        
        for metadata in videos_metadata:
            # Create task
            task = DownloadTask(
                task_id=str(uuid.uuid4()),
                url=f"https://www.youtube.com/watch?v={metadata.video_id}",
                video_id=metadata.video_id,
                title=metadata.title,
                quality=quality,
                status=TaskStatus.PENDING,
                progress=0.0,
                notification_settings=notification_settings,
                playlist_id=playlist_id,
                playlist_name=playlist_name or "Playlist",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            # Save to database
            await self._database.save_task(task)
            
            tasks.append(task)
            task_ids.append(task.task_id)
        
        # Track playlist tasks
        self._playlist_tasks[playlist_id] = task_ids
        
        # Enqueue tasks sequentially (they will be processed one by one)
        for task in tasks:
            await self._task_queue.enqueue(task)
        
        return playlist_id, tasks
    
    async def cancel_playlist(self, playlist_id: str) -> dict[str, int]:
        """
        Cancel all remaining tasks in a playlist
        
        Args:
            playlist_id: Playlist ID to cancel
            
        Returns:
            Dictionary with counts: {"cancelled": N, "already_completed": M}
            
        Requirements: 7.8
        """
        from bot.database import TaskStatus
        
        if playlist_id not in self._playlist_tasks:
            return {"cancelled": 0, "already_completed": 0}
        
        task_ids = self._playlist_tasks[playlist_id]
        cancelled = 0
        already_completed = 0
        
        for task_id in task_ids:
            task = await self._database.get_task(task_id)
            
            if task is None:
                continue
            
            # Skip already completed/failed/cancelled tasks
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                already_completed += 1
                continue
            
            # Cancel the task
            if await self.cancel_task(task_id):
                cancelled += 1
        
        return {"cancelled": cancelled, "already_completed": already_completed}
    
    async def get_playlist_report(self, playlist_id: str) -> dict:
        """
        Get summary report for a playlist
        
        Args:
            playlist_id: Playlist ID
            
        Returns:
            Dictionary with report data:
            {
                "total": int,
                "completed": int,
                "failed": int,
                "cancelled": int,
                "in_progress": int
            }
            
        Requirements: 4.7
        """
        from bot.database import TaskStatus
        
        if playlist_id not in self._playlist_tasks:
            return {
                "total": 0,
                "completed": 0,
                "failed": 0,
                "cancelled": 0,
                "in_progress": 0
            }
        
        task_ids = self._playlist_tasks[playlist_id]
        
        report = {
            "total": len(task_ids),
            "completed": 0,
            "failed": 0,
            "cancelled": 0,
            "in_progress": 0
        }
        
        for task_id in task_ids:
            task = await self._database.get_task(task_id)
            
            if task is None:
                continue
            
            if task.status == TaskStatus.COMPLETED:
                report["completed"] += 1
            elif task.status == TaskStatus.FAILED:
                report["failed"] += 1
            elif task.status == TaskStatus.CANCELLED:
                report["cancelled"] += 1
            elif task.status in [TaskStatus.PENDING, TaskStatus.DOWNLOADING, TaskStatus.PAUSED]:
                report["in_progress"] += 1
        
        return report

    
    async def restore_interrupted_tasks(self) -> dict:
        """
        Restore interrupted tasks after bot restart
        
        Marks tasks that were downloading/pending as interrupted
        and provides summary for user notification.
        
        Returns:
            Dictionary with restoration summary:
            {
                "interrupted_count": int,
                "tasks": list of interrupted tasks
            }
            
        Requirements: 10.5, 10.6
        """
        from bot.database import TaskStatus
        
        # Get tasks that were in progress
        downloading = await self._database.get_tasks_by_status(TaskStatus.DOWNLOADING)
        pending = await self._database.get_tasks_by_status(TaskStatus.PENDING)
        
        interrupted_tasks = downloading + pending
        
        # Mark them as interrupted
        for task in interrupted_tasks:
            task.status = TaskStatus.INTERRUPTED
            task.updated_at = datetime.now(timezone.utc)
            await self._database.update_task(task)
        
        return {
            "interrupted_count": len(interrupted_tasks),
            "tasks": interrupted_tasks
        }

    
    async def handle_storage_disconnection(self) -> dict:
        """
        Handle WebDAV storage disconnection
        
        Pauses all active tasks when storage becomes unavailable.
        
        Returns:
            Dictionary with handling summary:
            {
                "paused_count": int,
                "tasks": list of paused tasks
            }
            
        Requirements: 2.7, 10.3, 10.4
        """
        from bot.database import TaskStatus
        
        # Get active tasks
        active_tasks = await self.get_active_tasks()
        
        paused_tasks = []
        
        for task in active_tasks:
            if task.status == TaskStatus.DOWNLOADING:
                # Pause the task
                task.status = TaskStatus.PAUSED
                task.error_message = "Storage disconnected"
                task.updated_at = datetime.now(timezone.utc)
                await self._database.update_task(task)
                paused_tasks.append(task)
        
        # Notify owner about disconnection
        if self._notification_service:
            await self._notification_service.notify_storage_disconnected()
        
        return {
            "paused_count": len(paused_tasks),
            "tasks": paused_tasks
        }
