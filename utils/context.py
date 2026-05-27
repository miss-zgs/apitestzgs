"""
全局上下文管理器 + 变量解析器

职责：
1. 存储接口间共享的变量（如 Token、ID、提取的响应字段）
2. 支持 ${变量名} 语法，从上下文中替换变量值
3. 从响应 JSON 中通过 jsonpath 提取变量并存入上下文

使用方式：
    from utils.context import context, resolve_variables, extract_and_save

    # 存入变量
    context.set("token", "abc123")

    # 变量替换
    result = resolve_variables({"headers": {"Auth": "Bearer ${token}"}})
    # → {"headers": {"Auth": "Bearer abc123"}}

    # 从响应中提取变量
    extract_and_save(response_json, {"user_id": "$.data.id"})

    # 清空（测试结束时）
    context.clear()
"""
import re
import logging
from typing import Any

logger = logging.getLogger(__name__)

# 匹配 ${变量名} 的正则表达式
_VARIABLE_PATTERN = re.compile(r"\$\{(\w+)\}")


class Context:
    """
    全局上下文（单例模式）

    本质是一个字典，存储接口间共享的变量。
    同一次测试运行中所有用例共享同一个 Context 实例。
    """

    def __init__(self):
        self._variables = {}

    def set(self, key: str, value):
        """
        存入变量

        :param key: 变量名，如 "token"、"user_id"
        :param value: 变量值，可以是任意类型
        """
        self._variables[key] = value

    def get(self, key: str, default=None):
        """
        读取变量

        :param key: 变量名
        :param default: 不存在时的默认值
        :return: 变量值
        """
        return self._variables.get(key, default)

    def set_many(self, data: dict):
        """批量存入变量"""
        self._variables.update(data)

    def get_all(self) -> dict:
        """获取所有变量（用于调试）"""
        return dict(self._variables)

    def clear(self):
        """清空所有变量（测试结束时调用）"""
        self._variables.clear()

    def __contains__(self, key: str) -> bool:
        return key in self._variables

    def __repr__(self):
        return f"Context({self._variables})"


# 全局唯一实例，整个项目直接 import 使用
context = Context()


# ==================== 变量解析 ====================


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
    match = _VARIABLE_PATTERN.fullmatch(text)
    if match:
        var_name = match.group(1)
        value = context.get(var_name)
        if value is None:
            logger.warning("变量 '${%s}' 未定义，保持原样", var_name)
            return text
        return value

    def _replacer(m):
        var_name = m.group(1)
        value = context.get(var_name)
        if value is None:
            logger.warning("变量 '${%s}' 未定义，保持原样", var_name)
            return m.group(0)
        return str(value)

    return _VARIABLE_PATTERN.sub(_replacer, text)
