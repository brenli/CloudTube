#!/usr/bin/env python3
"""Check WebDAV token in database"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from bot.database import Database
from bot.config import ConfigManager


async def main():
    config = ConfigManager.load_from_env()
    db = Database(config.database_path)
    await db.initialize()
    
    webdav_config = await db.get_webdav_config()
    
    if webdav_config:
        print(f"URL: {webdav_config.url}")
        print(f"Username: {webdav_config.username}")
        print(f"Password prefix: {webdav_config.password[:10]}...")
        print(f"Password length: {len(webdav_config.password)}")
        
        is_oauth = webdav_config.password.startswith(("y0_", "t1.", "AQAA"))
        print(f"Is OAuth token: {is_oauth}")
        
        if not is_oauth:
            print("\n⚠️  ПРОБЛЕМА: В БД сохранен обычный пароль, а не OAuth токен!")
            print("Решение: Выполните команду в Telegram:")
            print(f"/connect {webdav_config.url} {webdav_config.username} <ваш_oauth_token>")
    else:
        print("WebDAV не настроен")
    
    await db.close()


if __name__ == "__main__":
    asyncio.run(main())
