"""
问题改写节点 - 当检索结果不相关时，改写用户问题以提升检索质量

使用 LLM 分析原始问题的语义意图，生成更精准的检索查询。
带有重试次数限制，避免无限循环。
包含 LLM API 重试逻辑以应对限流。
"""

import time
from rich.console import Console

from src.config import get_llm, MAX_RETRY_COUNT

console = Console()

# LLM 重试配置
MAX_LLM_RETRIES = 3
LLM_RETRY_DELAY = 2  # 秒


REWRITE_PROMPT = (
    "你是一个故障诊断查询优化专家。用户提出了一个关于车载系统故障的问题，"
    "但之前的检索结果不够相关。请分析原始问题的语义意图，"
    "生成一个更精准、更适合向量检索的查询。\n\n"
    "改写要求：\n"
    "1. 保留原始问题的核心意图\n"
    "2. 补充可能的同义词或专业术语\n"
    "3. 去除无关的修饰词\n"
    "4. 使查询更简洁、更聚焦于故障特征\n\n"
    "原始问题：\n-------\n{question}\n-------\n\n"
    "请直接输出改写后的查询，不要加任何解释。"
)


def _invoke_llm_with_retry(llm, messages):
    """带 retry 的 LLM 调用，应对 API 限流"""
    for attempt in range(MAX_LLM_RETRIES):
        try:
            return llm.invoke(messages)
        except Exception as e:
            if attempt < MAX_LLM_RETRIES - 1:
                console.print(
                    f"  [yellow]LLM 调用失败 (第{attempt + 1}次)，"
                    f"{LLM_RETRY_DELAY}s 后重试... 错误: {e}[/yellow]"
                )
                time.sleep(LLM_RETRY_DELAY)
            else:
                console.print(f"  [red]LLM 重试 {MAX_LLM_RETRIES} 次后仍失败: {e}[/red]")
                return None
    return None


def rewrite_node(state: dict) -> dict:
    """
    问题改写节点：改写用户问题以提升检索质量。
    """
    question = state.get("question", "")
    retry_count = state.get("retry_count", 0)

    console.print(
        f"\n[bold yellow][问题改写][/bold yellow] "
        f"第 {retry_count + 1}/{MAX_RETRY_COUNT} 次改写问题..."
    )

    start_time = time.time()

    llm = get_llm()
    prompt = REWRITE_PROMPT.format(question=question)

    response = _invoke_llm_with_retry(llm, [{"role": "user", "content": prompt}])

    elapsed = time.time() - start_time

    if response is None:
        # LLM 不可用时降级：使用原始问题
        console.print(f"  [red]LLM 不可用，使用原始问题重试[/red]")
        console.print(f"  [dim]耗时: {elapsed:.2f}s[/dim]")
        rewritten = question
    else:
        rewritten = response.content.strip()
        console.print(f"  [dim]改写后: {rewritten}[/dim]")
        console.print(f"  [dim]耗时: {elapsed:.2f}s[/dim]")

    return {
        "rewritten_question": rewritten,
        "retry_count": retry_count + 1,
    }
