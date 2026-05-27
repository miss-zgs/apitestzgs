"""
通用断言工具
支持状态码校验、jsonpath 提取校验、字段包含/类型校验等
"""
import logging
from typing import Any

from jsonpath_ng.ext import parse as jsonpath_parse

logger = logging.getLogger(__name__)


def assert_status_code(response, expected_code: int):
    """校验 HTTP 状态码"""
    actual = response.status_code
    assert actual == expected_code, (
        f"状态码不匹配: 期望 {expected_code}, 实际 {actual}\n"
        f"响应内容: {response.text[:500]}"
    )


def assert_json_field(response, field_path: str, expected_value: Any):
    """
    通过 jsonpath 提取字段并校验值

    :param response: requests.Response 对象
    :param field_path: jsonpath 表达式，如 $.code / $.data.list[0].name
    :param expected_value: 期望值
    """
    body = response.json()
    matches = jsonpath_parse(field_path).find(body)
    assert matches, f"jsonpath '{field_path}' 在响应中未匹配到任何值\n响应: {body}"
    actual = matches[0].value
    assert actual == expected_value, (
        f"字段 '{field_path}' 值不匹配: 期望 {expected_value!r}, 实际 {actual!r}"
    )


def assert_json_contains(response, field_path: str, keyword: str):
    """校验 jsonpath 提取的值包含指定关键词"""
    body = response.json()
    matches = jsonpath_parse(field_path).find(body)
    assert matches, f"jsonpath '{field_path}' 在响应中未匹配到任何值"
    actual = str(matches[0].value)
    assert keyword in actual, f"字段 '{field_path}' 的值 '{actual}' 不包含 '{keyword}'"


def assert_json_type(response, field_path: str, expected_type: type):
    """校验 jsonpath 提取的值类型"""
    body = response.json()
    matches = jsonpath_parse(field_path).find(body)
    assert matches, f"jsonpath '{field_path}' 在响应中未匹配到任何值"
    actual = matches[0].value
    assert isinstance(actual, expected_type), (
        f"字段 '{field_path}' 类型不匹配: 期望 {expected_type.__name__}, 实际 {type(actual).__name__}"
    )


def assert_json_not_empty(response, field_path: str):
    """校验 jsonpath 提取的值不为空"""
    body = response.json()
    matches = jsonpath_parse(field_path).find(body)
    assert matches, f"jsonpath '{field_path}' 在响应中未匹配到任何值"
    actual = matches[0].value
    assert actual, f"字段 '{field_path}' 的值为空: {actual!r}"


def extract_json_field(response, field_path: str) -> Any:
    """
    提取 jsonpath 对应的值（不做断言，仅返回）

    注意：如果需要提取变量并存入上下文供后续接口使用，
    请使用 utils.context.extract_and_save() 代替。
    """
    body = response.json()
    matches = jsonpath_parse(field_path).find(body)
    if not matches:
        logger.warning("jsonpath '%s' 未匹配到任何值", field_path)
        return None
    return matches[0].value


def assert_by_expect(response, expect: dict):
    """
    根据 expect 字典批量校验，用于数据驱动

    expect 格式示例:
    {
        "status_code": 200,
        "body": {
            "$.code": 0,
            "$.data.name": "张三"
        }
    }
    """
    if "status_code" in expect:
        assert_status_code(response, int(expect["status_code"]))

    body_checks = expect.get("body", {})
    if isinstance(body_checks, dict):
        for path, expected_value in body_checks.items():
            assert_json_field(response, path, expected_value)
