"""
规则校验节点 - 调用 validate_rules 工具基于 Business Schema 进行校验

对应简历中四阶段流水线的第三阶段：规则校验
从日志和检索结果中提取错误码，查询业务 Schema 中的校验规则。
"""

import re
import time
from rich.console import Console

from src.tools.rule_validator import validate_rules

console = Console()

# 错误码模式匹配（如 BMS_CHG_TIMEOUT_003, AEB_CONF_LOW_002 等）
ERROR_CODE_PATTERN = re.compile(r"[A-Z]+_[A-Z_]+_\d{3}")


def rule_check_node(state: dict) -> dict:
    """
    规则校验节点：从日志和检索结果中提取错误码，
    调用 validate_rules 工具查询业务规则。
    """
    log_data = state.get("log_data", "")
    retrieved_docs = state.get("retrieved_docs", "")

    console.print("\n[bold cyan][阶段3: 规则校验][/bold cyan] 正在提取错误码并校验业务规则...")

    start_time = time.time()

    # 从日志和检索结果中提取错误码
    combined_text = f"{log_data}\n{retrieved_docs}"
    error_codes = ERROR_CODE_PATTERN.findall(combined_text)
    # 去重
    error_codes = list(dict.fromkeys(error_codes))

    if not error_codes:
        console.print("  [yellow]未提取到错误码，跳过规则校验[/yellow]")
        elapsed = time.time() - start_time
        console.print(f"  [dim]耗时: {elapsed:.2f}s[/dim]")
        return {"rule_check_result": "未检测到已知错误码，无法执行业务规则校验。"}

    console.print(f"  [dim]提取到错误码: {', '.join(error_codes)}[/dim]")

    # 对每个错误码执行规则校验
    results = []
    for code in error_codes:
        result = validate_rules.invoke({"error_code": code})
        results.append(result)

    combined_result = "\n\n".join(results)
    elapsed = time.time() - start_time
    console.print(f"  [dim]规则校验完成 ({len(error_codes)} 个错误码) | 耗时: {elapsed:.2f}s[/dim]")

    return {"rule_check_result": combined_result}
