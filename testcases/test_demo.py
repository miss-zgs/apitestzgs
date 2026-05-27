"""
示例测试用例 - 数据驱动
使用 JSONPlaceholder 公开 API 进行演示
支持从 YAML / JSON / CSV 加载用例
支持接口依赖编排（串行执行 + 变量提取替换）
"""
import pytest
from testcases.conftest import load_cases
from utils.assertion import assert_by_expect
from utils.case_executor import execute_case, execute_chain, parse_csv_case


# ---------- YAML 驱动 ----------

@pytest.mark.parametrize(
    "case",
    load_cases("test_demo.yaml"),
    ids=lambda c: c.get("case_name", ""),
)
def test_yaml_driven(case, http_client):
    """YAML 数据驱动用例"""
    response = execute_case(case, http_client)
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
    response = execute_case(case, http_client)
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
    parsed_case = parse_csv_case(case)
    response = execute_case(parsed_case, http_client)
    if parsed_case.get("expect"):
        assert_by_expect(response, parsed_case["expect"])


# ---------- 接口依赖编排（串行执行） ----------

def test_dependency_chain(http_client):
    """
    接口依赖编排示例：按顺序执行多个接口，上一个接口的返回值传给下一个

    用例文件中通过 extract 提取变量，后续用例通过 ${变量名} 引用
    """
    execute_chain(load_cases("test_dependency.yaml"), http_client)


# ---------- 飞猪接口测试（串行执行） ----------

def test_fliggy_pickup_price(http_client):
    """飞猪道旅 - 接机查价接口"""
    execute_chain(load_cases("test_fliggy_pickup.yaml"), http_client)



