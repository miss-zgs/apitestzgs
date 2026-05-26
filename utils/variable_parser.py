"""
变量解析器

支持 ${变量名} 语法，从全局上下文中替换变量值。
用于接口依赖编排场景：前一个接口提取的值，后续接口通过 ${} 引用。

支持的数据类型：
    - 字符串中的变量替换：  "Bearer ${token}" → "Bearer abc123"
    - 字典中的递归替换：    {"Authorization": "Bearer ${token}"}
    - 列表中的递归替换：    ["${id1}", "${id2}"]
    - 纯变量引用（保留原始类型）：  "${user_id}" → 123（int，不是字符串）

使用方式：
    from utils.variable_parser import resolve_variables
    from utils.context import context

    context.set("token", "abc123")
    context.set("user_id", 42)

    result = resolve_variables({"headers": {"Auth": "Bearer ${token}"}, "id": "${user_id}"})
    # → {"headers": {"Auth": "Bearer abc123"}, "id": 42}
"""
import re
import logging
from typing import Any

from utils.context import context

logger = logging.getLogger(__name__)

# 匹配 ${变量名} 的正则表达式
_VARIABLE_PATTERN = re.compile(r"\$\{(\w+)\}")


def resolve_variables(data: Any) -> Any:
    """
    递归解析数据中的 ${变量名}，从全局上下文中替换

    :param data: 任意数据（字符串、字典、列表等）
    :return: 替换变量后的数据
    """
    if data is None:
        return None

    if isinstance(data, str):
        return _resolve_string(data)

    if isinstance(data, dict):
        return {key: resolve_variables(value) for key, value in data.items()}

    if isinstance(data, list):
        return [resolve_variables(item) for item in data]

    # 其他类型（int、float、bool 等）原样返回
    return data


def extract_and_save(response_json: dict, extract_rules: dict):
    """
    从响应 JSON 中提取变量并存入全局上下文

    :param response_json: 接口响应的 JSON 数据
    :param extract_rules: 提取规则字典，如 {"token": "$.data.token", "user_id": "$.data.id"}
    """
    from jsonpath_ng.ext import parse as jsonpath_parse

    for variable_name, jsonpath_expr in extract_rules.items():
        matches = jsonpath_parse(jsonpath_expr).find(response_json)
        if matches:
            value = matches[0].value
            context.set(variable_name, value)
            logger.info("提取变量: %s = %r (from %s)", variable_name, value, jsonpath_expr)
        else:
            logger.warning("提取变量失败: %s (jsonpath '%s' 未匹配)", variable_name, jsonpath_expr)


def _resolve_string(text: str) -> Any:
    """
    解析字符串中的 ${变量名}

    - 如果整个字符串就是一个变量引用（如 "${user_id}"），返回原始类型（int/list 等）
    - 如果字符串中包含变量和其他文本（如 "Bearer ${token}"），返回拼接后的字符串
    """
    # 情况1：整个字符串就是一个变量引用 → 保留原始类型
    match = _VARIABLE_PATTERN.fullmatch(text)
    if match:
        var_name = match.group(1)
        value = context.get(var_name)
        if value is None:
            logger.warning("变量 '${%s}' 未定义，保持原样", var_name)
            return text
        return value

    # 情况2：字符串中包含变量 → 字符串替换
    def _replacer(m):
        var_name = m.group(1)
        value = context.get(var_name)
        if value is None:
            logger.warning("变量 '${%s}' 未定义，保持原样", var_name)
            return m.group(0)
        return str(value)

    return _VARIABLE_PATTERN.sub(_replacer, text)
