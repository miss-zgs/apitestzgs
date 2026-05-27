"""
pytest 全局 fixture
"""
import os
import sys

import pytest

# 将项目根目录加入 sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import setup_logging
from utils.http_client import HttpClient
from utils.data_loader import load_test_data
from utils.context import context
from config.settings import get_env_var

# 项目启动时初始化日志（控制台 + 文件双输出）
setup_logging()


@pytest.fixture(scope="session", autouse=True)
def inject_env_variables():
    """
    将 .env 中的环境变量注入全局上下文，
    用例中可通过 ${FLIGGY_CLIENT_ID} 等语法引用
    """
    import time
    env_keys = [
        "FLIGGY_CLIENT_ID",
        "FLIGGY_CLIENT_SECRET",
        "FLIGGY_ENV",
    ]
    for key in env_keys:
        value = get_env_var(key)
        if value:
            context.set(key, value)

    # 注入时间戳变量，用于生成唯一订单号（如 resellerOrderNo）
    context.set("timestamp", str(int(time.time())))


@pytest.fixture(scope="session")
def http_client():
    """全局共享的 HTTP 客户端实例"""
    client = HttpClient()
    yield client
    client.clear_session()
    context.clear()


def load_cases(file_name: str):
    """
    便捷加载 data/ 目录下的用例数据，用于 @pytest.mark.parametrize

    用法:
        @pytest.mark.parametrize("case", load_cases("test_demo.yaml"), ids=lambda c: c.get("case_name", ""))
        def test_xxx(case, http_client):
            ...
    """
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    file_path = os.path.join(data_dir, file_name)
    return load_test_data(file_path)
