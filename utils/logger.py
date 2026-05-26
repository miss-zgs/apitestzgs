"""
日志初始化模块

本模块的作用：配置 Python logging 系统，让日志同时输出到控制台和文件。
在项目启动时调用一次 setup_logging() 即可全局生效，其他模块无需任何修改。

工作原理：
    Python 的 logging 模块采用 "Logger → Handler → Formatter" 三层结构：
    - Logger（记录器）：负责产生日志，如 logger.info("xxx")
    - Handler（处理器）：负责决定日志输出到哪里（控制台？文件？）
    - Formatter（格式器）：负责决定日志长什么样

    本模块给根 Logger 挂了两个 Handler：
    ┌─────────────┐
    │   Logger    │  ← http_client.py 里的 logger.info() 产生日志
    └──────┬──────┘
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
 控制台        文件
(终端看)   (logs/yyyy-MM-dd.log)

日志文件存放位置：项目根目录/logs/
文件命名格式：yyyy-MM-dd.log（如 2026-05-27.log）
自动保留最近 30 天，超过的自动删除。

使用方式：
    from utils.logger import setup_logging
    setup_logging()  # 调一次就行，后续所有 logging 调用都会自动输出到控制台+文件
"""
import logging
import os
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler

from config.settings import get_project_root, load_config

# 日志文件存放目录：项目根目录/logs/
_LOG_DIR = os.path.join(get_project_root(), "logs")


def setup_logging():
    """
    初始化全局日志配置（整个项目只需调用一次）

    执行步骤：
    1. 创建 logs/ 目录（不存在则自动创建）
    2. 从 config.yaml 读取日志级别和格式
    3. 给根 Logger 添加两个 Handler：控制台 + 文件
    4. 屏蔽第三方库的 DEBUG 噪音日志
    """

    # ========== 第1步：确保 logs 目录存在 ==========
    # exist_ok=True 表示如果目录已存在不报错
    os.makedirs(_LOG_DIR, exist_ok=True)

    # ========== 第2步：从 config.yaml 读取日志配置 ==========
    config = load_config()

    # 日志级别：DEBUG 会记录所有信息，INFO 只记录关键信息
    # config.yaml 里配置的是字符串 "DEBUG" 或 "INFO"，需要转成 logging 模块的常量
    log_level_str = config.get("logging", {}).get("level", "INFO")
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)
    # getattr(logging, "DEBUG") → logging.DEBUG (值为 10)
    # getattr(logging, "INFO")  → logging.INFO  (值为 20)

    # 日志格式模板
    # %(asctime)s   → 时间，如 2026-05-27 15:49:13,457
    # %(levelname)s → 级别，如 INFO、DEBUG、WARNING
    # %(name)s      → 记录器名称，如 utils.http_client
    # %(message)s   → 日志内容，如 ">>> [GET] https://xxx"
    log_format = config.get("logging", {}).get(
        "format",
        "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
    )

    # ========== 第3步：配置根 Logger ==========
    # 根 Logger 是所有 Logger 的父级，设置它就等于设置了全局默认行为
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # 防护：如果已经初始化过（比如被调用了两次），直接返回，避免重复添加 Handler
    if root_logger.handlers:
        return

    # ========== 第4步：屏蔽第三方库的噪音日志 ==========
    # 这些库在 DEBUG 级别下会输出大量无用信息，只保留 WARNING 以上
    for noisy_lib in ("faker", "urllib3", "charset_normalizer", "asyncio"):
        logging.getLogger(noisy_lib).setLevel(logging.WARNING)

    # ========== 第5步：创建日志格式器 ==========
    # 控制台和文件使用同一种格式
    formatter = logging.Formatter(log_format)

    # ========== 第6步：添加控制台 Handler ==========
    # StreamHandler 默认输出到 sys.stderr（终端屏幕）
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)       # 控制台显示的最低级别
    console_handler.setFormatter(formatter)   # 设置输出格式
    root_logger.addHandler(console_handler)   # 挂到根 Logger 上

    # ========== 第7步：添加文件 Handler ==========
    # 按天生成日志文件，如 logs/2026-05-27.log
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(_LOG_DIR, f"{today}.log")

    # TimedRotatingFileHandler：定时切分文件的 Handler
    file_handler = TimedRotatingFileHandler(
        filename=log_file,      # 日志文件路径
        when="midnight",        # 切分时机：每天午夜（00:00）自动切到新文件
        interval=1,             # 间隔：每 1 天切分一次
        backupCount=30,         # 保留最近 30 个旧文件，超过的自动删除
        encoding="utf-8",       # 文件编码，支持中文
    )
    file_handler.setLevel(log_level)       # 文件记录的最低级别
    file_handler.setFormatter(formatter)   # 设置输出格式
    root_logger.addHandler(file_handler)   # 挂到根 Logger 上

    # 输出一条初始化成功的日志，同时验证双输出是否正常工作
    logging.info("日志初始化完成，日志文件: %s", log_file)
