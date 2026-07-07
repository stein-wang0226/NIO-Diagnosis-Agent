"""
知识检索节点 - 调用 retrieve_cases 和 fetch_test_data 工具检索历史案例和测试数据

对应简历中四阶段流水线的第二阶段：知识检索
"""

import time
from rich.console import Console

from src.tools.knowledge_retriever import retrieve_cases, fetch_test_data

console = Console()


def retrieve_node(state: dict) -> dict:
    """
    知识检索节点：从历史案例知识库和测试报告中检索相关信息。
    使用用户问题（或改写后的问题）进行检索。
    """
    # 优先使用改写后的问题
    query = state.get("rewritten_question") or state.get("question", "")

    console.print("\n[bold cyan][阶段2: 知识检索][/bold cyan] 正在检索历史案例和测试数据...")

    start_time = time.time()

    # 检索历史案例（向量检索）
    cases_result = retrieve_cases.invoke({"query": query})
    console.print(f"  [dim]历史案例检索完成 ({len(cases_result)} 字符)[/dim]")

    # 检索测试报告
    test_data_result = fetch_test_data.invoke({"query": query})
    console.print(f"  [dim]测试数据检索完成 ({len(test_data_result)} 字符)[/dim]")

    elapsed = time.time() - start_time

    # 合并检索结果
    combined_docs = f"=== 历史案例 ===\n{cases_result}\n\n=== 测试报告 ===\n{test_data_result}"

    console.print(f"  [dim]检索完成 | 耗时: {elapsed:.2f}s[/dim]")

    return {
        "retrieved_docs": combined_docs,
        "rewritten_question": "",  # 清空改写后的问题，避免重复使用
    }
