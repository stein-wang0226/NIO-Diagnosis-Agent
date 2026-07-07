"""
原因分析节点 - 综合日志、历史案例、规则校验结果，由 LLM 生成诊断报告

对应简历中四阶段流水线的第四阶段：原因分析
这是整个 Agent 的最终输出环节，输出结构化的诊断报告。
包含 LLM API 重试逻辑以应对限流。
"""

import time
from rich.console import Console

from src.config import get_llm

console = Console()

# LLM 重试配置
MAX_LLM_RETRIES = 3
LLM_RETRY_DELAY = 2  # 秒


ANALYZE_PROMPT = (
    "你是蔚来汽车效能平台的高级故障诊断专家。\n"
    "请根据以下信息，综合分析故障原因并生成诊断报告。\n\n"
    "## 用户问题\n{question}\n\n"
    "## 异常日志\n{log_data}\n\n"
    "## 历史案例与测试报告\n{retrieved_docs}\n\n"
    "## 业务规则校验结果\n{rule_check_result}\n\n"
    "## 要求\n"
    "请按以下格式输出诊断报告：\n\n"
    "### 故障概述\n（简要描述故障现象）\n\n"
    "### 根因分析\n（分析故障的根本原因，结合日志、历史案例和规则校验结果）\n\n"
    "### 关联组件\n（列出涉及的组件及其依赖关系）\n\n"
    "### 解决方案\n（基于历史案例给出推荐的解决方案）\n\n"
    "### 风险评估\n（评估故障严重度和潜在影响）\n\n"
    "### 复盘建议\n（给出后续测试和预防建议）\n\n"
    "注意：\n"
    "- 如果信息不足以确定根因，请明确说明需要哪些额外信息\n"
    "- 引用历史案例时请标注案例编号\n"
    "- 使用专业但易懂的语言"
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
                return None
    return None


def analyze_node(state: dict) -> dict:
    """
    原因分析节点：综合所有信息生成诊断报告。
    """
    question = state.get("question", "")
    log_data = state.get("log_data", "无日志数据")
    retrieved_docs = state.get("retrieved_docs", "无历史案例")
    rule_check_result = state.get("rule_check_result", "无规则校验结果")

    console.print("\n[bold cyan][阶段4: 原因分析][/bold cyan] 正在综合分析并生成诊断报告...")

    start_time = time.time()

    llm = get_llm()
    prompt = ANALYZE_PROMPT.format(
        question=question,
        log_data=log_data[:4000],
        retrieved_docs=retrieved_docs[:4000],
        rule_check_result=rule_check_result[:2000],
    )

    response = _invoke_llm_with_retry(llm, [{"role": "user", "content": prompt}])

    elapsed = time.time() - start_time

    if response is None:
        # LLM 不可用时的降级：输出原始数据摘要
        report = (
            "## 诊断报告（降级模式 - LLM 不可用）\n\n"
            "由于 LLM 服务暂时不可用，无法生成 AI 分析报告。\n"
            "以下是原始数据摘要：\n\n"
            f"### 异常日志摘要\n{log_data[:1000]}\n\n"
            f"### 历史案例摘要\n{retrieved_docs[:1000]}\n\n"
            f"### 规则校验摘要\n{rule_check_result[:1000]}\n"
        )
        console.print(f"  [red]LLM 不可用，输出降级报告[/red]")
        console.print(f"  [dim]耗时: {elapsed:.2f}s[/dim]")
    else:
        report = response.content
        console.print(f"  [green]诊断报告生成完成[/green]")
        console.print(f"  [dim]耗时: {elapsed:.2f}s[/dim]")

    return {"diagnosis_report": report}
