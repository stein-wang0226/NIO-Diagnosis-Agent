"""
日志获取工具 - 从 Mock 日志数据中按条件筛选异常日志

模拟蔚来效能平台中"日志自动拉取"能力，
从本地 JSON 文件中按错误码、组件、级别等条件筛选日志。
"""

import json
from langchain.tools import tool

from src.config import ANOMALY_LOGS_PATH


def _load_logs() -> list[dict]:
    """加载所有异常日志"""
    with open(str(ANOMALY_LOGS_PATH), "r", encoding="utf-8") as f:
        return json.load(f)


@tool
def fetch_logs(query: str) -> str:
    """
    从车载系统异常日志库中检索与问题相关的日志记录。
    输入关于异常现象、错误码或组件名的描述，
    返回匹配的日志详情（含时间戳、级别、错误码、堆栈、上下文）。
    """
    logs = _load_logs()
    query_lower = query.lower()

    # 关键词匹配
    matched = []
    for log in logs:
        searchable_fields = [
            log.get("component", ""),
            log.get("error_code", ""),
            log.get("message", ""),
            log.get("context", ""),
            log.get("log_id", ""),
            log.get("vehicle_id", ""),
        ]
        searchable = " ".join(searchable_fields).lower()
        keywords = query_lower.split()
        if any(kw in searchable for kw in keywords):
            matched.append(log)

    # 如果没匹配到，返回所有 ERROR 级别日志
    if not matched:
        matched = [log for log in logs if log.get("level") == "ERROR"]

    if not matched:
        return "未找到相关日志记录。"

    # 去重（按 log_id）
    seen_ids = set()
    unique = []
    for log in matched:
        lid = log.get("log_id", "")
        if lid not in seen_ids:
            seen_ids.add(lid)
            unique.append(log)

    results = []
    for log in unique:
        results.append(
            f"日志ID: {log['log_id']}\n"
            f"时间: {log['timestamp']} | 级别: {log['level']} | 组件: {log['component']}\n"
            f"ECU: {log['ecu']} | 车辆: {log['vehicle_id']} | 版本: {log['software_version']}\n"
            f"错误码: {log['error_code']}\n"
            f"消息: {log['message']}\n"
            f"堆栈: {log['stack_trace']}\n"
            f"CAN信号: {log['can_signal']}\n"
            f"上下文: {log['context']}\n"
        )

    return "\n---\n".join(results)
