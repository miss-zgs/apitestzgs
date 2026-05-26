"""
示例测试用例 - 数据驱动
使用 JSONPlaceholder 公开 API 进行演示
支持从 YAML / JSON / CSV 加载用例
"""
import json
import pytest
from testcases.conftest import load_cases
from utils.assertion import assert_by_expect


# ---------- YAML 驱动 ----------

@pytest.mark.parametrize(
    "case",
    load_cases("test_demo.yaml"),
    ids=lambda c: c.get("case_name", ""),
)
def test_yaml_driven(case, http_client):
    """YAML 数据驱动用例"""
    response = _execute_case(case, http_client)
    if case.get("expect"):
        assert_by_expect(response, case["expect"])


# ---------- JSON 驱动 ----------

@pytest.mark.parametrize(
    "case",
    load_cases("test_demo.json"),
    ids=lambda c: c.get("case_name", ""),
)
def test_json_driven(case, http_client):
    """JSON 数据驱动用例"""
    response = _execute_case(case, http_client)
    if case.get("expect"):
        assert_by_expect(response, case["expect"])


# ---------- CSV 驱动 ----------

@pytest.mark.parametrize(
    "case",
    load_cases("test_demo.csv"),
    ids=lambda c: c.get("case_name", ""),
)
def test_csv_driven(case, http_client):
    """CSV 数据驱动用例"""
    # CSV 读出来的 json/expect 字段是字符串，需要反序列化
    parsed_case = _parse_csv_case(case)
    response = _execute_case(parsed_case, http_client)
    if parsed_case.get("expect"):
        assert_by_expect(response, parsed_case["expect"])


# ---------- 通用执行逻辑 ----------

def _execute_case(case: dict, http_client) -> "requests.Response":
    """根据用例字典执行请求"""
    method = case.get("method", "GET").upper()
    url = case.get("url", "")
    params = case.get("params")
    json_data = case.get("json")
    headers = case.get("headers")
    data = case.get("data")

    kwargs = {}
    if headers:
        kwargs["headers"] = headers

    if method == "GET":
        return http_client.get(url, params=params, **kwargs)
    elif method == "POST":
        return http_client.post(url, data=data, json_data=json_data, **kwargs)
    elif method == "PUT":
        return http_client.put(url, data=data, json_data=json_data, **kwargs)
    elif method == "DELETE":
        return http_client.delete(url, **kwargs)
    elif method == "PATCH":
        return http_client.patch(url, data=data, json_data=json_data, **kwargs)
    else:
        raise ValueError(f"不支持的请求方法: {method}")


def _parse_csv_case(case: dict) -> dict:
    """CSV 用例的字符串字段反序列化为 dict"""
    parsed = dict(case)
    for field in ("json", "expect", "params", "headers"):
        value = parsed.get(field)
        if isinstance(value, str) and value.strip():
            try:
                parsed[field] = json.loads(value)
            except json.JSONDecodeError:
                pass
    return parsed
