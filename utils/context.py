"""
全局上下文管理器

用于接口间传递数据（如登录后的 Token、创建资源后的 ID 等）。
前一个接口通过 extract 提取的变量会存入上下文，后续接口通过 ${变量名} 引用。

使用方式：
    from utils.context import context

    # 存入变量
    context.set("token", "abc123")

    # 读取变量
    token = context.get("token")  # → "abc123"

    # 清空（测试结束时）
    context.clear()
"""


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
