"""
pytest 全局 fixture
"""
import logging
import sys
import os

import pytest

# 将项目根目录加入 sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.http_client import HttpClient
from utils.data_loader import load_test_data


@pytest.fixture(scope="session")
def http_client():
    """全局共享的 HTTP 客户端实例"""
    client = HttpClient()
    yield client
    client.clear_session()


@pytest.fixture(scope="session")
def autouse_logging():
    """统一日志格式"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )


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
