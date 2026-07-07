"""
LangGraph 图组装 - 将四阶段诊断流水线组装为 StateGraph

图结构：
  START → log_fetch → retrieve → grade_docs → (relevant?) 
                                              ├─ yes → rule_check → analyze → END
                                              └─ no  → rewrite → retrieve (循环)
"""

from typing import TypedDict, Annotated
from operator import add

from langgraph.graph import StateGraph, END, START

from src.nodes.log_fetch_node import log_fetch_node
from src.nodes.retrieve_node import retrieve_node
from src.nodes.grade_node import grade_node, route_after_grading
from src.nodes.rewrite_node import rewrite_node
from src.nodes.rule_check_node import rule_check_node
from src.nodes.analyze_node import analyze_node


# ============================================
# State 定义
# ============================================
class DiagnosisState(TypedDict):
    """Agent 诊断状态"""
    question: str                      # 用户原始问题
    log_data: str                      # 拉取的日志数据
    retrieved_docs: str                # 检索到的历史案例和测试报告（序列化为 str 以避免 LangGraph 状态序列化问题）
    is_relevant: bool                  # 文档评分结果
    rewritten_question: str            # 改写后的问题
    rule_check_result: str             # 规则校验结果
    diagnosis_report: str              # 最终诊断报告
    retry_count: int                   # 重试次数
    messages: Annotated[list, add]     # 消息历史（累加模式）


# ============================================
# 图组装
# ============================================
def build_graph():
    """
    构建诊断 Agent 的 LangGraph 图。

    流程：
    1. log_fetch: 从日志库拉取异常日志
    2. retrieve: 向量检索历史案例 + 关键词检索测试报告
    3. grade_documents: 评估检索结果相关性
       - 相关 → rule_check → analyze → END
       - 不相关 → rewrite → retrieve (循环，最多3次)
    """
    workflow = StateGraph(DiagnosisState)

    # 添加节点
    workflow.add_node("log_fetch", log_fetch_node)
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("grade", grade_node)
    workflow.add_node("rewrite", rewrite_node)
    workflow.add_node("rule_check", rule_check_node)
    workflow.add_node("analyze", analyze_node)

    # 添加边：主流程
    workflow.add_edge(START, "log_fetch")
    workflow.add_edge("log_fetch", "retrieve")
    workflow.add_edge("retrieve", "grade")

    # 条件边：grade 节点评分后，由 route_after_grading 决定路由
    # 相关 → rule_check；不相关且未达重试上限 → rewrite
    workflow.add_conditional_edges(
        "grade",
        route_after_grading,
        {
            "rule_check": "rule_check",
            "rewrite": "rewrite",
        },
    )

    # 循环边：改写后重新检索（retry_count < MAX_RETRY_COUNT 由 grade_node 控制）
    workflow.add_edge("rewrite", "retrieve")

    # 最终流程
    workflow.add_edge("rule_check", "analyze")
    workflow.add_edge("analyze", END)

    # 编译图
    graph = workflow.compile()
    return graph


def get_graph():
    """获取编译后的图实例（单例）"""
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


_graph = None


def print_graph_structure():
    """打印图结构信息"""
    from rich.console import Console
    from rich.panel import Panel

    console = Console()
    structure = """
[bold]NIO Diagnosis Agent - LangGraph 图结构[/bold]

  START
    |
    v
  [log_fetch] ---- 日志自动获取（阶段1）
    |
    v
  [retrieve] ---- 知识检索（阶段2）
    |
    v
  [grade] ---- 文档评分（条件路由）
    |                    ^
    | 相关/重试上限       |
    +-- 不相关 --> [rewrite] --+
    |                    (最多重试3次)
    |相关
    v
  [rule_check] ---- 规则校验（阶段3）
    |
    v
  [analyze] ---- 原因分析（阶段4）
    |
    v
   END
    """
    console.print(Panel(structure, title="Agent 图结构", border_style="cyan"))


def get_mermaid_diagram() -> str:
    """生成 Mermaid 格式的图可视化"""
    return """graph TB
    START([START]) --> log_fetch[日志获取<br/>阶段1: log_fetch]
    log_fetch --> retrieve[知识检索<br/>阶段2: retrieve]
    retrieve --> grade[文档评分<br/>grade]
    grade -->|相关| rule_check[规则校验<br/>阶段3: rule_check]
    grade -->|不相关 & retry < 3| rewrite[问题改写<br/>rewrite]
    rewrite --> retrieve
    rule_check --> analyze[原因分析<br/>阶段4: analyze]
    analyze --> END([END])
"""


if __name__ == "__main__":
    print_graph_structure()
    graph = build_graph()
    print("\n图编译成功！")
    print("\nMermaid 可视化：")
    print(get_mermaid_diagram())
