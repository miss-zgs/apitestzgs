"""
接口层基类
所有业务接口类继承此基类，统一使用 HttpClient 发送请求
"""
from typing import Optional

import requests

from utils.http_client import HttpClient


class BaseApi:
    """接口基类，提供便捷的请求方法和通用能力"""

    def __init__(self, client: Optional[HttpClient] = None):
        self.client = client or HttpClient()

    def get(self, path: str, params: dict = None, **kwargs) -> requests.Response:
        return self.client.get(path, params=params, **kwargs)

    def post(self, path: str, json_data: dict = None, **kwargs) -> requests.Response:
        return self.client.post(path, json_data=json_data, **kwargs)

    def put(self, path: str, json_data: dict = None, **kwargs) -> requests.Response:
        return self.client.put(path, json_data=json_data, **kwargs)

    def delete(self, path: str, **kwargs) -> requests.Response:
        return self.client.delete(path, **kwargs)

    def patch(self, path: str, json_data: dict = None, **kwargs) -> requests.Response:
        return self.client.patch(path, json_data=json_data, **kwargs)

    def set_token(self, token: str, prefix: str = "Bearer"):
        self.client.set_token(token, prefix)
