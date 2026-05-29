"""
Bug 报告工具

标准化的 Bug 记录方法，当用例执行失败时自动收集请求、响应、报错、环境等信息，
按统一 Markdown 模板追加写入 BUGFIX.md。

使用方式：
    # 自动模式 —— 在 case_executor 中断言失败时自动调用
    # 手动模式 ——
    from utils.bug_reporter import report_bug
    report_bug(
        bug_title="创单返回价格不一致",
        severity="高",
        case_name="接机创单",
        request_info={"method": "POST", "url": "https://...", "headers": {...}, "body": {...}},
        response_info={"status_code": 200, "body": {...}, "elapsed": 2.451},
        error_message="AssertionError: ...",
    )
"""
import json
import logging
import os
import platform
import re
import sys
import traceback
from datetime import datetime
from typing import Optional

from config.settings import get_project_root

logger = logging.getLogger(__name__)

# Bug 记录文件路径
_BUGFIX_PATH = os.path.join(get_project_root(), "BUGFIX.md")

# 需要脱敏的 Header 关键词（不区分大小写）
_SENSITIVE_KEYS = {"secret", "password", "token", "authorization", "cookie"}


def report_bug(
    bug_title: str,
    severity: str = "高",
    case_name: str = "",
    case_file: str = "",
    step_info: str = "",
    request_info: Optional[dict] = None,
    response_info: Optional[dict] = None,
    error_message: str = "",
    traceback_str: str = "",
    request_id: str = "",
    root_cause: str = "待分析",
    run_command: str = "",
):
    """
    记录一个 Bug 到 BUGFIX.md

    :param bug_title: Bug 标题
    :param severity: 严重程度（高/中/低）
    :param case_name: 用例名称
    :param case_file: 用例数据文件（如 data/test_fliggy_pickup.yaml）
    :param step_info: 步骤信息（如 "步骤 2/3"）
    :param request_info: 请求信息 {"method", "url", "headers", "body"}
    :param response_info: 响应信息 {"status_code", "body", "elapsed"}
    :param error_message: 报错信息
    :param traceback_str: 完整堆栈（如不传，自动从当前异常捕获）
    :param request_id: 请求唯一 Key（如 R-c076）
    :param root_cause: 原因分析
    :param run_command: 复现命令
    """
    bug_id = _next_bug_id()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    severity_icon = {"高": "🔴", "中": "🟡", "低": "🟢"}.get(severity, "⚪")

    # 自动捕获堆栈（如果调用方没传）
    if not traceback_str:
        traceback_str = traceback.format_exc()
        if traceback_str == "NoneType: None\n":
            traceback_str = ""

    # 收集环境信息
    env_info = _collect_env_info()

    # 收集上下文变量快照
    context_snapshot = _collect_context_snapshot()

    # 构建报告内容
    lines = []
    lines.append(f"## BUG-{bug_id:03d}：{bug_title}\n")
    lines.append(f"- **发现时间**：{now}")
    lines.append(f"- **严重程度**：{severity_icon} {severity}")
    lines.append(f"- **状态**：❌ 待修复")
    if request_id:
        lines.append(f"- **请求唯一 Key**：{request_id}")
    lines.append("")

    # 报错位置
    lines.append("### 报错位置")
    if case_name:
        lines.append(f"- **用例名称**：{case_name}")
    if case_file:
        file_desc = case_file
        if step_info:
            file_desc += f"（{step_info}）"
        lines.append(f"- **用例文件**：{file_desc}")
    if traceback_str:
        trigger_location = _extract_trigger_location(traceback_str)
        if trigger_location:
            lines.append(f"- **触发位置**：{trigger_location}")
    lines.append("")

    # 环境信息
    lines.append("### 环境信息")
    for key, value in env_info.items():
        lines.append(f"- **{key}**：{value}")
    lines.append("")

    # 请求信息
    if request_info:
        lines.append("### 请求信息")
        lines.append(f"- **Method**：{request_info.get('method', 'N/A')}")
        lines.append(f"- **URL**：{request_info.get('url', 'N/A')}")
        headers = request_info.get("headers")
        if headers:
            lines.append(f"- **Headers**：")
            lines.append("  ```json")
            lines.append(f"  {json.dumps(_mask_sensitive(headers), ensure_ascii=False)}")
            lines.append("  ```")
        body = request_info.get("body")
        if body:
            lines.append(f"- **Body**：")
            lines.append("  ```json")
            lines.append(f"  {_format_json(body)}")
            lines.append("  ```")
        lines.append("")

    # 响应信息
    if response_info:
        lines.append("### 响应信息")
        lines.append(f"- **Status Code**：{response_info.get('status_code', 'N/A')}")
        elapsed = response_info.get("elapsed")
        if elapsed is not None:
            lines.append(f"- **耗时**：{elapsed}s")
        resp_body = response_info.get("body")
        if resp_body:
            lines.append(f"- **Response Body**：")
            lines.append("  ```json")
            lines.append(f"  {_format_json(resp_body)}")
            lines.append("  ```")
        lines.append("")

    # 报错信息
    if error_message:
        lines.append("### 报错信息")
        lines.append("```")
        lines.append(error_message.strip())
        lines.append("```")
        lines.append("")

    # 完整堆栈
    if traceback_str:
        lines.append("### 完整堆栈")
        lines.append("```")
        lines.append(traceback_str.strip())
        lines.append("```")
        lines.append("")

    # 上下文变量快照
    if context_snapshot:
        lines.append("### 上下文变量快照")
        lines.append("```json")
        lines.append(json.dumps(context_snapshot, ensure_ascii=False, indent=2))
        lines.append("```")
        lines.append("")

    # 原因分析
    lines.append("### 原因分析")
    lines.append(root_cause)
    lines.append("")

    # 复现步骤
    lines.append("### 复现步骤")
    if run_command:
        lines.append(f"```bash\n{run_command}\n```")
    else:
        lines.append("```bash\npython3 -m pytest testcases/ -v\n```")
    lines.append("")
    lines.append("---\n")

    report_content = "\n".join(lines)

    # 写入文件
    _append_to_bugfix(report_content)

    logger.warning("🐛 已记录 BUG-%03d: %s → %s", bug_id, bug_title, _BUGFIX_PATH)


# ==================== 辅助方法 ====================


def _next_bug_id() -> int:
    """读取 BUGFIX.md 中已有的最大 Bug 编号，返回下一个编号"""
    if not os.path.isfile(_BUGFIX_PATH):
        return 1

    max_id = 0
    with open(_BUGFIX_PATH, "r", encoding="utf-8") as file:
        for line in file:
            match = re.match(r"## BUG-(\d+)", line)
            if match:
                bug_num = int(match.group(1))
                if bug_num > max_id:
                    max_id = bug_num
    return max_id + 1


def _collect_env_info() -> dict:
    """收集运行环境信息"""
    from config.settings import get_current_env, get_base_url

    return {
        "运行环境": get_current_env(),
        "Base URL": get_base_url(),
        "Python 版本": sys.version.split()[0],
        "操作系统": f"{platform.system()} {platform.machine()}",
    }


def _collect_context_snapshot() -> dict:
    """收集上下文变量快照（脱敏处理）"""
    from utils.context import context

    all_vars = context.get_all()
    if not all_vars:
        return {}
    return _mask_sensitive(all_vars)


def _mask_sensitive(data: dict) -> dict:
    """对敏感字段进行脱敏（保留前 3 字符 + ***）"""
    masked = {}
    for key, value in data.items():
        if any(s in key.lower() for s in _SENSITIVE_KEYS):
            str_val = str(value)
            if len(str_val) > 3:
                masked[key] = str_val[:3] + "***"
            else:
                masked[key] = "***"
        else:
            masked[key] = value
    return masked


def _format_json(data) -> str:
    """格式化 JSON 输出（dict → 紧凑 JSON 字符串，其他原样）"""
    if isinstance(data, (dict, list)):
        return json.dumps(data, ensure_ascii=False)
    return str(data)


def _extract_trigger_location(traceback_str: str) -> str:
    """从堆栈中提取最后一个项目文件的位置（排除第三方库）"""
    project_root = get_project_root()
    lines = traceback_str.strip().split("\n")

    last_project_file = ""
    for line in lines:
        line = line.strip()
        if line.startswith("File ") and project_root in line:
            # 提取文件名和行号：File "/path/to/file.py", line 72, in func_name
            match = re.search(r'File "(.+?)", line (\d+), in (.+)', line)
            if match:
                file_path = match.group(1).replace(project_root + "/", "")
                line_num = match.group(2)
                func_name = match.group(3)
                last_project_file = f"{file_path}::{func_name} (line {line_num})"
    return last_project_file


def _append_to_bugfix(content: str):
    """追加内容到 BUGFIX.md"""
    # 如果文件不存在，先写标题
    if not os.path.isfile(_BUGFIX_PATH):
        with open(_BUGFIX_PATH, "w", encoding="utf-8") as file:
            file.write("# Bug 记录\n\n")

    with open(_BUGFIX_PATH, "a", encoding="utf-8") as file:
        file.write(content)
