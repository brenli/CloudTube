# Проверка алгоритма создания, монтирования и загрузки

## 📋 Общий алгоритм

### 1. Создание точки монтирования `/mnt/yandex-disk`

#### Код (bot/webdav.py, строки 63-70):
```python
# Create mount point with sudo if doesn't exist
if not os.path.exists(MOUNT_POINT):
    logger.info(f"Creating mount point {MOUNT_POINT}")
    process = await asyncio.create_subprocess_shell(
        f"sudo mkdir -p {MOUNT_POINT}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    await process.communicate()
```

#### ✅ Проверка:
- **Путь**: `/mnt/yandex-disk` (константа MOUNT_POINT, строка 20)
- **Создание**: Автоматическое через `sudo mkdir -p`
- **Условие**: Только если каталог не существует
- **Права**: Создается с правами root, но монтируется с uid/gid пользователя

#### ⚠️ Потенциальная проблема:
Каталог создается с правами root. Нужно установить владельца после создания.

#### 🔧 Рекомендация:
```python
# После создания каталога добавить:
if not os.path.exists(MOUNT_POINT):
    logger.info(f"Creating mount point {MOUNT_POINT}")
    process = await asyncio.create_subprocess_shell(
        f"sudo mkdir -p {MOUNT_POINT}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    await process.communicate()
    
    # Установить владельца
    username = os.getenv('USER') or os.getenv('USERNAME')
    process = await asyncio.create_subprocess_shell(
        f"sudo chown {username}:{username} {MOUNT_POINT}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    await process.communicate()
    logger.info(f"Set owner of {MOUNT_POINT} to {username}")
```

---

### 2. Настройка davfs2

#### Код (bot/webdav.py, строки 107-141):
```python
async def _setup_davfs2(self) -> None:
    # Get home directory - use HOME env var or fallback
    home_dir = os.environ.get('HOME')
    if not home_dir:
        user = os.environ.get('USER', 'root')
        if user == 'root':
            home_dir = '/root'
        else:
            home_dir = f'/home/{user}'
    
    davfs2_dir = os.path.join(home_dir, '.davfs2')
    logger.info(f"Using davfs2 directory: {davfs2_dir}")
    
    # Create .davfs2 directory
    os.makedirs(davfs2_dir, exist_ok=True)
    
    # Update global paths
    global DAVFS2_SECRETS, DAVFS2_CONFIG
    DAVFS2_SECRETS = os.path.join(davfs2_dir, 'secrets')
    DAVFS2_CONFIG = os.path.join(davfs2_dir, 'davfs2.conf')
    
    # Create config file if doesn't exist
    if not os.path.exists(DAVFS2_CONFIG):
        config_content = """# davfs2 configuration
use_locks 0
cache_size 50
delay_upload 0
"""
        with open(DAVFS2_CONFIG, 'w') as f:
            f.write(config_content)
```

#### ✅ Проверка:
- **Определение HOME**: Из переменной окружения или fallback
- **Создание каталога**: `~/.davfs2/` с exist_ok=True
- **Конфигурация**: Создается автоматически если не существует
- **Глобальные переменные**: Обновляются динамически

#### ✅ Корректность:
Алгоритм правильный. Использует переменную HOME из systemd сервиса.

---

### 3. Сохранение учетных данных

#### Код (bot/webdav.py, строки 143-160):
```python
async def _save_credentials(self) -> None:
    secrets_content = f"{self._config.url} {self._config.username} {self._config.password}\n"
    
    logger.info(f"Saving credentials to {DAVFS2_SECRETS}")
    
    with open(DAVFS2_SECRETS, 'w') as f:
        f.write(secrets_content)
    
    # Set proper permissions (600)
    os.chmod(DAVFS2_SECRETS, 0o600)
```

#### ✅ Проверка:
- **Формат**: `URL username password` (стандарт davfs2)
- **Права**: 600 (только владелец может читать/писать)
- **Путь**: Динамический из _setup_davfs2()

#### ✅ Корректность:
Алгоритм правильный. Формат соответствует требованиям davfs2.

---

### 4. Монтирование WebDAV

#### Код (bot/webdav.py, строки 162-213):
```python
async def _mount_webdav(self) -> bool:
    # Check if already mounted
    if await self._is_mounted_check():
        logger.info("WebDAV already mounted")
        return True
    
    # Get current user and group
    import pwd
    username = os.getenv('USER') or os.getenv('USERNAME')
    user_info = pwd.getpwnam(username)
    uid = user_info.pw_uid
    gid = user_info.pw_gid
    
    logger.info(f"Mounting as user: {username} (uid={uid}, gid={gid})")
    
    # Mount command with sudo and uid/gid options
    cmd = f"sudo mount -t davfs {self._config.url} {MOUNT_POINT} -o uid={uid},gid={gid}"
    
    logger.info(f"Mounting WebDAV: {cmd}")
    
    # Execute mount command
    process = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        stdin=asyncio.subprocess.PIPE
    )
    
    # Send empty line for any prompts
    stdout, stderr = await process.communicate(input=b'\n\n')
    
    # Check return code
    if process.returncode != 0:
        error_msg = stderr.decode() if stderr else "Unknown error"
        logger.error(f"Mount failed: {error_msg}")
        return False
    
    # Wait for mount to complete
    await asyncio.sleep(2)
    
    # Verify mount
    is_mounted = await self._is_mounted_check()
    logger.info(f"Mount verification: {is_mounted}")
    
    return is_mounted
```

#### ✅ Проверка:
- **Проверка существующего монтирования**: Да, через _is_mounted_check()
- **Получение uid/gid**: Из pwd модуля (корректно)
- **Команда монтирования**: `sudo mount -t davfs URL MOUNT_POINT -o uid=X,gid=Y`
- **Обработка ввода**: Отправка пустых строк для пропуска интерактивных запросов
- **Проверка результата**: Через return code и повторную проверку
- **Задержка**: 2 секунды для завершения монтирования

#### ✅ Корректность:
Алгоритм правильный. Монтирование с правильными uid/gid обеспечивает доступ пользователя.

---

### 5. Проверка монтирования

#### Код (bot/webdav.py, строки 215-230):
```python
async def _is_mounted_check(self) -> bool:
    try:
        # Check if mount point exists and is accessible
        if not os.path.exists(MOUNT_POINT):
            return False
        
        # Try to list directory
        try:
            os.listdir(MOUNT_POINT)
            return True
        except OSError:
            return False
    
    except Exception:
        return False
```

#### ✅ Проверка:
- **Существование каталога**: Проверяется
- **Доступность**: Проверяется через os.listdir()
- **Обработка ошибок**: Корректная

#### ✅ Корректность:
Алгоритм правильный. Надежная проверка монтирования.

---

### 6. Загрузка файла

#### Код (bot/webdav.py, строки 310-370):
```python
async def upload_file(
    self,
    local_path: str,
    remote_path: str,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> bool:
    if not self._is_mounted:
        raise ConnectionError("Not connected to WebDAV storage")
    
    # Get file size
    file_size = os.path.getsize(local_path)
    logger.info(f"Uploading file: {local_path} ({file_size} bytes / {file_size/1024/1024:.1f} MB) to {remote_path}")
    
    # Build full destination path
    dest_path = os.path.join(MOUNT_POINT, remote_path.lstrip('/'))
    
    # Create directory if needed
    dest_dir = os.path.dirname(dest_path)
    if dest_dir:
        logger.info(f"Creating directory: {dest_dir}")
        os.makedirs(dest_dir, exist_ok=True)
    
    # Copy file with progress tracking for large files
    logger.info(f"Copying file to {dest_path}")
    
    if file_size > 10 * 1024 * 1024 and progress_callback:  # > 10MB
        # Copy in chunks with progress
        chunk_size = 1024 * 1024  # 1MB chunks
        bytes_copied = 0
        
        with open(local_path, 'rb') as src:
            with open(dest_path, 'wb') as dst:
                while True:
                    chunk = src.read(chunk_size)
                    if not chunk:
                        break
                    dst.write(chunk)
                    bytes_copied += len(chunk)
                    
                    # Call progress callback
                    if progress_callback:
                        await progress_callback(bytes_copied, file_size)
                    
                    # Small delay to avoid blocking
                    if bytes_copied % (10 * 1024 * 1024) == 0:  # Every 10MB
                        await asyncio.sleep(0.01)
    else:
        # Small file, copy directly
        shutil.copy2(local_path, dest_path)
        
        # Call progress callback with final progress
        if progress_callback:
            await progress_callback(file_size, file_size)
    
    logger.info("Upload completed successfully")
    return True
```

#### ✅ Проверка:
- **Проверка монтирования**: Да, через self._is_mounted
- **Построение пути**: `os.path.join(MOUNT_POINT, remote_path.lstrip('/'))`
- **Создание каталогов**: Автоматическое через os.makedirs(exist_ok=True)
- **Копирование**: 
  - Большие файлы (>10MB): Чанками по 1MB с прогрессом
  - Маленькие файлы: Прямое копирование через shutil.copy2
- **Прогресс**: Callback вызывается для каждого чанка
- **Задержка**: Каждые 10MB для избежания блокировки

#### ✅ Корректность:
Алгоритм правильный. Эффективная загрузка с отслеживанием прогресса.

---

### 7. Формирование путей для загрузки

#### Код (bot/download.py, строки 654-661):
```python
# Determine remote path based on playlist membership
if task.playlist_id and task.playlist_name:
    # Part of a playlist - organize in playlist folder
    # Sanitize playlist name for filesystem
    safe_playlist_name = self._task_executor.webdav_service.sanitize_filename(task.playlist_name)
    remote_path = f"{safe_playlist_name}/{os.path.basename(local_path)}"
else:
    # Single video - save in "Single Videos" folder
    remote_path = f"Single Videos/{os.path.basename(local_path)}"
```

#### ✅ Проверка:
- **Плейлист**: `{sanitized_playlist_name}/{filename.mp4}`
- **Одиночное видео**: `Single Videos/{filename.mp4}`
- **Санитизация**: Через sanitize_filename() - удаляет недопустимые символы

#### ✅ Корректность:
Алгоритм правильный. Правильная организация файлов.

---

## 🎯 Итоговая структура на диске

После загрузки файлы будут организованы так:

```
/mnt/yandex-disk/                    # Точка монтирования
├── Single Videos/                   # Отдельные видео
│   ├── Video Title 1.mp4
│   ├── Video Title 2.mp4
│   └── Another Video.mp4
└── My Awesome Playlist/             # Плейлисты (имя санитизировано)
    ├── Episode 1.mp4
    ├── Episode 2.mp4
    └── Episode 3.mp4
```

На Яндекс.Диске (https://disk.yandex.ru):
```
/
├── Single Videos/
│   └── ...
└── My Awesome Playlist/
    └── ...
```

---

## 🔍 Полный поток выполнения

### Команда: `/connect https://webdav.yandex.ru email@yandex.ru token`

1. **bot_handler.py** → `handle_connect()`
2. **webdav.py** → `connect(config)`
   - Создает `/mnt/yandex-disk` если не существует ✅
   - Вызывает `_setup_davfs2()` → создает `~/.davfs2/` ✅
   - Вызывает `_save_credentials()` → сохраняет в `~/.davfs2/secrets` ✅
   - Вызывает `_mount_webdav()` → монтирует с uid/gid ✅
   - Вызывает `test_connection()` → проверяет доступность ✅
3. **database.py** → `save_webdav_config()` → сохраняет в БД ✅

### Отправка ссылки на видео: `https://youtube.com/watch?v=...`

1. **bot_handler.py** → `_handle_message()` → показывает выбор качества
2. Пользователь выбирает качество и уведомления
3. **download.py** → `create_download_task()`
   - Извлекает метаданные через yt-dlp ✅
   - Создает задачу в БД ✅
   - Добавляет в очередь ✅
4. **download.py** → `TaskQueue._process_task()`
   - Скачивает видео во временную директорию ✅
   - Формирует remote_path: `Single Videos/{filename}` ✅
   - Вызывает `webdav.upload_file()` ✅
5. **webdav.py** → `upload_file()`
   - Строит путь: `/mnt/yandex-disk/Single Videos/{filename}` ✅
   - Создает каталог `Single Videos/` если не существует ✅
   - Копирует файл чанками с прогрессом ✅
6. **download.py** → обновляет статус задачи на COMPLETED ✅
7. **download.py** → удаляет временный файл ✅

---

## ⚠️ Найденные проблемы

### 1. Права на точку монтирования

**Проблема**: Каталог `/mnt/yandex-disk` создается с правами root.

**Решение**: Добавить установку владельца после создания.

**Код для исправления** (bot/webdav.py, после строки 70):
```python
# After creating mount point, set owner
if not os.path.exists(MOUNT_POINT):
    logger.info(f"Creating mount point {MOUNT_POINT}")
    process = await asyncio.create_subprocess_shell(
        f"sudo mkdir -p {MOUNT_POINT}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    await process.communicate()
    
    # Set owner to current user
    username = os.getenv('USER') or os.getenv('USERNAME')
    if username:
        process = await asyncio.create_subprocess_shell(
            f"sudo chown {username}:{username} {MOUNT_POINT}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()
        logger.info(f"Set owner of {MOUNT_POINT} to {username}")
```

### 2. Проверка существования каталога перед созданием

**Текущий код**: Проверяет только существование, но не права доступа.

**Рекомендация**: Добавить проверку прав доступа.

---

## ✅ Общая оценка

### Корректность алгоритма: 95/100

**Плюсы:**
- ✅ Автоматическое создание всех необходимых каталогов
- ✅ Правильное монтирование с uid/gid
- ✅ Корректная обработка учетных данных
- ✅ Надежная проверка монтирования
- ✅ Эффективная загрузка с прогрессом
- ✅ Правильная организация файлов
- ✅ Санитизация имен файлов

**Минусы:**
- ⚠️ Права на точку монтирования не устанавливаются явно
- ⚠️ Нет проверки прав доступа к существующему каталогу

**Рекомендации:**
1. Добавить установку владельца для `/mnt/yandex-disk`
2. Добавить проверку прав доступа
3. Все остальное работает корректно

---

## 📝 Итоговый вердикт

**Алгоритм создания, монтирования и загрузки КОРРЕКТЕН и готов к использованию.**

Единственное улучшение - добавить установку владельца для точки монтирования.

---

**Дата проверки:** 2026-03-18  
**Проверил:** Kiro AI Assistant  
**Статус:** ✅ ОДОБРЕНО с минорными рекомендациями
