"""
统一 HTTP 请求封装模块

本模块是整个接口自动化框架的核心，提供统一的 HTTP 请求发送能力。
所有接口请求都应通过 HttpClient 类发出，而不是直接使用 requests 库。

核心能力:
    - 统一封装 GET / POST / PUT / DELETE / PATCH / 文件上传 六种请求方式
    - 自动拼接 base_url + path，也支持传入完整 URL
    - 请求失败自动重试（重试次数和间隔可在 config.yaml 中配置）
    - 自动记录请求和响应日志，方便排查问题
    - 基于 requests.Session 的会话管理，自动保持 Cookie
    - 全局 Header 管理，便捷设置 Token / Authorization

使用示例:
    # 基本用法
    client = HttpClient()
    response = client.get("/api/user/info", params={"id": 1})
    response = client.post("/api/user/create", json_data={"name": "test"})

    # 设置 Token
    client.set_token("your_token_here")

    # 指定其他环境的 base_url
    client = HttpClient(base_url="https://other-api.example.com")
"""
import json
import logging
import time
from typing import Optional, Union

import requests
import urllib3

from config.settings import get_base_url, get_timeout, get_request_config

# 关闭 SSL 未验证的警告提示，避免在 verify_ssl=False 时控制台大量刷屏
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 模块级别的日志记录器，日志名称为 utils.http_client
logger = logging.getLogger(__name__)


class HttpClient:
    """
    统一 HTTP 客户端

    所有接口请求都通过此类发出，提供以下核心能力:
    1. 请求方法封装：get / post / put / delete / patch / upload
    2. 自动重试：请求异常时按配置自动重试
    3. 日志记录：自动记录每次请求的 URL、方法、参数、响应状态码和耗时
    4. Session 管理：基于 requests.Session，自动维护 Cookie 等会话状态
    5. Header 管理：支持全局默认 Header 和单次请求自定义 Header 的合并
    """

    def __init__(self, base_url: Optional[str] = None, timeout: Optional[int] = None):
        """
        初始化 HTTP 客户端

        :param base_url: 接口的基础地址（如 https://api.example.com），
                         不传则从 config.yaml 中读取当前环境的 base_url
        :param timeout: 请求超时时间（秒），不传则从配置文件读取
        """
        # 基础地址：优先使用传入的值，否则从配置文件读取当前环境的地址
        self.base_url = base_url or get_base_url()

        # 从配置文件读取全局请求配置（重试次数、重试间隔、是否验证 SSL 等）
        request_config = get_request_config()

        # 请求超时时间（秒）
        self.timeout = timeout or get_timeout()

        # 请求失败后的最大重试次数（默认 2 次）
        self.retry_count = request_config.get("retry_count", 2)

        # 每次重试之间的等待间隔（秒，默认 1 秒）
        self.retry_interval = request_config.get("retry_interval", 1)

        # 是否验证 SSL 证书（测试环境通常设为 False）
        self.verify_ssl = request_config.get("verify_ssl", False)

        # requests.Session 实例，自动维护 Cookie、连接池等会话状态
        self.session = requests.Session()

        # 默认请求头，所有请求都会携带，可通过 set_headers() 追加或覆盖
        self._default_headers = {"Content-Type": "application/json"}

    # ==================== 公开方法（对外提供的请求接口） ====================

    def get(self, path: str, params: dict = None, **kwargs) -> requests.Response:
        """
        发送 GET 请求

        :param path: 接口路径（如 /api/user/info）或完整 URL
        :param params: URL 查询参数，如 {"page": 1, "size": 10} → ?page=1&size=10
        :param kwargs: 其他参数（headers、cookies 等），透传给 requests
        :return: requests.Response 响应对象
        """
        return self._request("GET", path, params=params, **kwargs)

    def post(self, path: str, data: Union[dict, str, None] = None,
             json_data: dict = None, **kwargs) -> requests.Response:
        """
        发送 POST 请求

        :param path: 接口路径或完整 URL
        :param data: 表单数据（application/x-www-form-urlencoded 格式）
        :param json_data: JSON 请求体（会自动序列化为 JSON 字符串）
        :param kwargs: 其他参数，透传给 requests
        :return: requests.Response 响应对象

        注意: data 和 json_data 二选一，json_data 用于发送 JSON 格式的请求体，
              data 用于发送表单格式的请求体
        """
        return self._request("POST", path, data=data, json=json_data, **kwargs)

    def put(self, path: str, data: Union[dict, str, None] = None,
            json_data: dict = None, **kwargs) -> requests.Response:
        """
        发送 PUT 请求（通常用于全量更新资源）

        :param path: 接口路径或完整 URL
        :param data: 表单数据
        :param json_data: JSON 请求体
        :param kwargs: 其他参数，透传给 requests
        :return: requests.Response 响应对象
        """
        return self._request("PUT", path, data=data, json=json_data, **kwargs)

    def delete(self, path: str, **kwargs) -> requests.Response:
        """
        发送 DELETE 请求（通常用于删除资源）

        :param path: 接口路径或完整 URL
        :param kwargs: 其他参数，透传给 requests
        :return: requests.Response 响应对象
        """
        return self._request("DELETE", path, **kwargs)

    def patch(self, path: str, data: Union[dict, str, None] = None,
              json_data: dict = None, **kwargs) -> requests.Response:
        """
        发送 PATCH 请求（通常用于部分更新资源）

        :param path: 接口路径或完整 URL
        :param data: 表单数据
        :param json_data: JSON 请求体
        :param kwargs: 其他参数，透传给 requests
        :return: requests.Response 响应对象
        """
        return self._request("PATCH", path, data=data, json=json_data, **kwargs)

    def upload(self, path: str, files: dict, data: dict = None, **kwargs) -> requests.Response:
        """
        文件上传请求

        上传文件时需要使用 multipart/form-data 格式，因此会自动移除默认的
        Content-Type: application/json 头，让 requests 库根据文件内容自动设置正确的
        Content-Type（包含 boundary 分隔符）。

        :param path: 接口路径或完整 URL
        :param files: 文件字典，格式如 {"file": open("test.png", "rb")}
                      或 {"file": ("filename.png", file_bytes, "image/png")}
        :param data: 随文件一起提交的表单字段
        :param kwargs: 其他参数，透传给 requests
        :return: requests.Response 响应对象
        """
        # 确保 headers 中不带 Content-Type，否则 multipart boundary 会出错
        kwargs.setdefault("headers", {})
        kwargs["headers"].pop("Content-Type", None)
        return self._request("POST", path, data=data, files=files, **kwargs)

    # ==================== Session / Header 管理 ====================

    def set_headers(self, headers: dict):
        """
        追加或覆盖全局默认 headers

        设置后，后续所有请求都会自动携带这些 header。
        如果 key 已存在则覆盖，不存在则新增。

        :param headers: 要设置的 header 字典，如 {"X-Custom": "value"}
        """
        self._default_headers.update(headers)

    def set_token(self, token: str, prefix: str = "Bearer"):
        """
        便捷设置 Authorization 请求头

        设置后，后续所有请求都会自动携带 Authorization 头。

        :param token: Token 字符串
        :param prefix: Token 前缀，默认 "Bearer"，最终格式为 "Bearer xxx"
                       如果是其他认证方式，可传 "Token"、"Basic" 等
        """
        self._default_headers["Authorization"] = f"{prefix} {token}"

    def clear_session(self):
        """
        清空会话状态

        重置 Session（清除 Cookie、连接池等）并恢复默认 headers。
        通常在测试结束后调用，避免会话状态污染后续测试。
        """
        self.session = requests.Session()
        self._default_headers = {"Content-Type": "application/json"}

    # ==================== 内部实现（私有方法） ====================

    def _build_url(self, path: str) -> str:
        """
        拼接完整的请求 URL

        如果 path 已经是完整 URL（以 http:// 或 https:// 开头），则直接返回；
        否则将 base_url 和 path 拼接起来，自动处理多余的斜杠。

        :param path: 接口路径（如 /api/user）或完整 URL
        :return: 完整的请求 URL

        示例:
            base_url = "https://api.example.com"
            _build_url("/api/user")  → "https://api.example.com/api/user"
            _build_url("https://other.com/api")  → "https://other.com/api"
        """
        if path.startswith(("http://", "https://")):
            return path
        return f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"

    def _merge_headers(self, extra_headers: Optional[dict]) -> dict:
        """
        合并请求头：默认 headers + 单次请求的自定义 headers

        单次请求传入的 headers 优先级更高，会覆盖默认值中同名的 key。

        :param extra_headers: 单次请求额外传入的 headers（可以为 None）
        :return: 合并后的 headers 字典
        """
        # 先复制一份默认 headers（避免修改原始数据）
        headers = dict(self._default_headers)
        if extra_headers:
            # 用单次请求的 headers 覆盖默认值
            headers.update(extra_headers)
        return headers

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        """
        核心请求方法 —— 所有公开方法最终都调用此方法

        执行流程:
        1. 拼接完整 URL
        2. 合并 headers（默认 + 自定义）
        3. 设置超时和 SSL 验证
        4. 发送请求，失败则按配置重试
        5. 记录请求和响应日志
        6. 返回响应对象

        :param method: HTTP 方法（GET / POST / PUT / DELETE / PATCH）
        :param path: 接口路径或完整 URL
        :param kwargs: 透传给 requests.Session.request() 的所有参数
        :return: requests.Response 响应对象
        :raises requests.RequestException: 所有重试都失败后抛出最后一次的异常
        """
        # 1. 拼接完整 URL
        url = self._build_url(path)

        # 2. 合并请求头
        kwargs["headers"] = self._merge_headers(kwargs.get("headers"))

        # 3. 设置默认超时和 SSL 验证（如果调用方没有显式指定的话）
        kwargs.setdefault("timeout", self.timeout)
        kwargs.setdefault("verify", self.verify_ssl)

        # 4. 带重试的请求发送
        last_exception = None
        for attempt in range(1, self.retry_count + 1):
            try:
                # 记录请求日志
                self._log_request(method, url, attempt, kwargs)

                # 记录开始时间，用于计算请求耗时
                start_time = time.time()

                # 通过 session 发送请求（自动维护 Cookie 等会话状态）
                response = self.session.request(method, url, **kwargs)

                # 计算请求耗时（保留 3 位小数）
                elapsed = round(time.time() - start_time, 3)

                # 记录响应日志
                self._log_response(response, elapsed)

                # 请求成功，直接返回响应
                return response
            except requests.RequestException as exc:
                # 请求失败，记录异常并判断是否继续重试
                last_exception = exc
                logger.warning("请求失败 [%s/%s]: %s", attempt, self.retry_count, exc)
                if attempt < self.retry_count:
                    # 还有重试机会，等待一段时间后继续
                    time.sleep(self.retry_interval)

        # 所有重试都失败了，抛出最后一次的异常
        raise last_exception

    @staticmethod
    def _log_request(method: str, url: str, attempt: int, kwargs: dict):
        """
        记录请求日志

        以 INFO 级别记录请求方法、URL 和重试次数；
        以 DEBUG 级别记录请求体和查询参数（避免 INFO 日志过于冗长）。

        :param method: HTTP 方法
        :param url: 完整请求 URL
        :param attempt: 当前是第几次尝试
        :param kwargs: 请求参数字典
        """
        logger.info(">>> [%s] %s (attempt %s)", method, url, attempt)
        # 请求体可能在 json 或 data 字段中
        body = kwargs.get("json") or kwargs.get("data")
        if body:
            logger.debug("    Body: %s", json.dumps(body, ensure_ascii=False) if isinstance(body, dict) else body)
        if kwargs.get("params"):
            logger.debug("    Params: %s", kwargs["params"])

    @staticmethod
    def _log_response(response: requests.Response, elapsed: float):
        """
        记录响应日志

        以 INFO 级别记录状态码、URL 和耗时；
        以 DEBUG 级别记录响应体（JSON 格式优先，否则截取前 500 字符的文本）。

        :param response: requests.Response 响应对象
        :param elapsed: 请求耗时（秒）
        """
        logger.info("<<< [%s] %s (%.3fs)", response.status_code, response.url, elapsed)
        try:
            # 尝试以 JSON 格式记录响应体
            logger.debug("    Response: %s", response.json())
        except ValueError:
            # 如果响应不是 JSON 格式，截取前 500 字符记录
            logger.debug("    Response: %s", response.text[:500])
