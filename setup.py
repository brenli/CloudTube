from setuptools import setup, find_packages

setup(
    name="youtube-webdav-bot",
    version="0.1.0",
    description="Telegram bot for downloading YouTube videos to WebDAV storage",
    author="Your Name",
    python_requires=">=3.11",
    packages=find_packages(exclude=["tests", "tests.*"]),
    install_requires=[
        "python-telegram-bot==21.0.1",
        "yt-dlp==2024.3.10",
        "webdav4==0.9.8",
        "aiosqlite==0.20.0",
        "cryptography==42.0.5",
        "psutil==5.9.8",
        "python-dotenv==1.0.1",
    ],
    extras_require={
        "dev": [
            "pytest==8.1.1",
            "pytest-asyncio==0.23.6",
            "pytest-cov==5.0.0",
            "hypothesis==6.100.0",
            "flake8==7.0.0",
            "mypy==1.9.0",
            "black==24.3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "youtube-webdav-bot=bot.main:main",
        ],
    },
)
