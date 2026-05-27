"""
用例执行引擎

提供通用的用例执行逻辑，所有测试文件都可以直接 import 使用。
支持：
    - ${变量名} 语法自动替换
    - extract 字段从响应中提取变量
    - base_url 字段指定独立域名
    - CSV 字段反序列化
"""
import json
import logging
from typing import List

import requests

from utils.context import resolve_variables, extract_and_save
from utils.assertion import assert_by_expect

logger = logging.getLogger(__name__)


def execute_case(case: dict, http_client) -> requests.Response:
    """
    根据用例字典执行请求

    支持：
    1. ${变量名} 语法 — 自动从上下文中替换变量
    2. extract 字段 — 从响应中提取值存入上下文供后续用例使用
    3. base_url 字段 — 用例可指定独立的域名（如飞猪接口）

    :param case: 用例字典
    :param http_client: HttpClient 实例
    :return: 响应对象
    """
    # 输出当前执行的用例名称
    case_name = case.get("case_name", "未命名用例")
    logger.info("========== 执行用例: %s ==========", case_name)

    # 1. 变量替换：将用例中的 ${xxx} 替换为上下文中的实际值
    resolved = resolve_variables(case)

    method = resolved.get("method", "GET").upper()
    url = resolved.get("url", "")
    params = resolved.get("params")
    json_data = resolved.get("json")
    headers = resolved.get("headers")
    data = resolved.get("data")
    case_base_url = resolved.get("base_url")

    # 2. 如果用例指定了 base_url，拼接完整 URL
    if case_base_url:
        url = case_base_url.rstrip("/") + "/" + url.lstrip("/")

    kwargs = {}
    if headers:
        kwargs["headers"] = headers

    if method == "GET":
        response = http_client.get(url, params=params, **kwargs)
    elif method == "POST":
        response = http_client.post(url, data=data, json_data=json_data, **kwargs)
    elif method == "PUT":
        response = http_client.put(url, data=data, json_data=json_data, **kwargs)
    elif method == "DELETE":
        response = http_client.delete(url, **kwargs)
    elif method == "PATCH":
        response = http_client.patch(url, data=data, json_data=json_data, **kwargs)
    else:
        raise ValueError(f"不支持的请求方法: {method}")

    # 3. 提取变量：如果用例中有 extract 字段，从响应中提取值存入上下文
    extract_rules = resolved.get("extract")
    if extract_rules:
        try:
            response_json = response.json()
            extract_and_save(response_json, extract_rules)
        except ValueError:
            pass

    return response


def execute_chain(cases: List[dict], http_client):
    """
    串行执行多个用例（接口依赖编排）

    按顺序执行，每个用例执行完后自动提取变量，后续用例自动引用。

    :param cases: 用例列表
    :param http_client: HttpClient 实例
    """
    for case in cases:
        response = execute_case(case, http_client)
        # expect 已在 execute_case 内的 resolve_variables 中解析过，
        # 但 execute_case 只处理请求相关字段，expect 需要单独解析（因为变量可能在前面步骤才提取）
        expect = case.get("expect")
        if expect:
            assert_by_expect(response, resolve_variables(expect))


def parse_csv_case(case: dict) -> dict:
    """
    CSV 用例的字符串字段反序列化为 dict

    CSV 读出来的 json/expect/params/headers 字段是字符串，需要 json.loads 转为 dict。

    :param case: 原始用例字典
    :return: 反序列化后的用例字典
    """
    parsed = dict(case)
    for field in ("json", "expect", "params", "headers"):
        value = parsed.get(field)
        if isinstance(value, str) and value.strip():
            try:
                parsed[field] = json.loads(value)
            except json.JSONDecodeError:
                pass
    return parsed
