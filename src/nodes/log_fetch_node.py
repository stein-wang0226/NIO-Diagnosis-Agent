"""
日志获取节点 - 调用 fetch_logs 工具从 Mock 日志库中拉取异常日志

对应简历中四阶段流水线的第一阶段：日志自动获取
"""

import time
from rich.console import Console

from src.tools.log_fetcher import fetch_logs

console = Console()


def log_fetch_node(state: dict) -> dict:
    """
    日志获取节点：根据用户问题从日志库中拉取相关异常日志。
    """
    question = state.get("question", "")
    console.print("\n[bold cyan][阶段1: 日志获取][/bold cyan] 正在从日志库拉取异常日志...")

    start_time = time.time()
    log_data = fetch_logs.invoke({"query": question})
    elapsed = time.time() - start_time

    console.print(f"  [dim]获取到日志数据 ({len(log_data)} 字符) | 耗时: {elapsed:.2f}s[/dim]")

    return {
        "log_data": log_data,
        "messages": [{"role": "system", "content": "[日志数据已获取]"}],
    }
