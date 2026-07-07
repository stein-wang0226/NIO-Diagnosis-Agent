"""
NIO Diagnosis Agent - 交互式 CLI 入口

使用 rich 库美化终端输出，支持多轮对话交互。
展示 Agent 每一步的决策过程和最终诊断报告。
"""

import sys

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.rule import Rule

from src.config import print_config, LLM_PROVIDER
from src.graph import build_graph, print_graph_structure

console = Console()

# 示例问题
EXAMPLE_QUESTIONS = [
    "BMS 充电握手超时，CML 报文延迟 12s，帮我分析原因",
    "AEB 在强光环境下没有触发制动，置信度只有 0.72，怎么回事？",
    "NOMI 多轮对话上下文丢失，第3轮对话找不到导航目的地",
    "OTA 断点续传失败，下载到 60% 中断后从头开始下载",
    "LKA 弯道居中偏移 0.35m 超出阈值，R250m 弯道处",
    "BMS 高温降温延迟，液冷泵 15s 才启动",
    "BMS 电芯电压不均衡，压差 80mV 超出 50mV 阈值",
    "ACC 前车正常减速时误触发 AEB 紧急制动",
    "HUD 导航箭头延迟 2s 显示，转弯时已过路口",
    "雨天路面 VCU 扭矩分配不均，左右轮扭矩差 30Nm 车辆跑偏",
    "BMS SOC 显示 30% 实际 22%，续航估算偏差大",
    "盲区检测漏检，侧后方摩托车 BSM 未报警",
    "蓝牙配对耗时 15s 超出 5s 超时阈值",
    "动能回收力度波动，减速度在 0.1g 到 0.3g 之间跳变",
    "BMS 绝缘电阻降至 50kΩ 低于 100kΩ 安全阈值",
    "前向碰撞预警延迟 1.5s，FCW 报警太晚",
    "VCU 电压采样异常，报文丢失 3 帧",
    "空气悬挂漏气，车身高度下降 30mm",
    "方向盘低速转弯有咔咔异响，EPS 电机温度报警",
    "空调压缩机不工作，出风口无冷风",
]


def print_banner():
    """打印欢迎横幅"""
    banner = """
[bold cyan]
  ╔══════════════════════════════════════════════════════════════╗
  ║          NIO Diagnosis Agent - AI 智能诊断系统              ║
  ║          基于 LangChain + LangGraph 的 RAG Agent             ║
  ║          蔚来效能平台 - 故障智能分析                         ║
  ╚══════════════════════════════════════════════════════════════╝
[/bold cyan]
"""
    console.print(banner)


def print_example_questions():
    """打印示例问题"""
    console.print("\n[bold]示例问题（直接输入序号即可）：[/bold]")
    for i, q in enumerate(EXAMPLE_QUESTIONS, 1):
        console.print(f"  [cyan]{i}.[/cyan] {q}")
    console.print()


def run_diagnosis(graph, question: str):
    """执行一次完整的诊断流程"""
    console.print(Rule(f"[bold]开始诊断: {question}[/bold]", style="cyan"))

    # 初始化状态
    initial_state = {
        "question": question,
        "log_data": "",
        "retrieved_docs": "",
        "is_relevant": False,
        "rewritten_question": "",
        "rule_check_result": "",
        "diagnosis_report": "",
        "retry_count": 0,
        "messages": [],
    }

    try:
        # 执行图
        final_state = graph.invoke(initial_state, {"recursion_limit": 25})

        # 输出诊断报告
        console.print(Rule("[bold]诊断报告[/bold]", style="green"))
        report = final_state.get("diagnosis_report", "未能生成诊断报告")

        try:
            console.print(Panel(Markdown(report), title="AI 诊断报告", border_style="green"))
        except Exception:
            console.print(Panel(report, title="AI 诊断报告", border_style="green"))

        # 输出执行摘要
        console.print("\n[bold]执行摘要：[/bold]")
        console.print(f"  原始问题: {question}")
        console.print(f"  重试次数: {final_state.get('retry_count', 0)}")
        log_len = len(final_state.get("log_data", ""))
        docs_len = len(final_state.get("retrieved_docs", ""))
        rule_len = len(final_state.get("rule_check_result", ""))
        console.print(f"  日志数据: {log_len} 字符")
        console.print(f"  检索结果: {docs_len} 字符")
        console.print(f"  规则校验: {rule_len} 字符")
        console.print(f"  评分结果: {'相关' if final_state.get('is_relevant') else '不相关'}")

    except Exception as e:
        console.print(f"\n[red]诊断过程出错: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")


def main():
    """主入口：交互式 CLI"""
    print_banner()

    # 检查 LLM 配置
    if LLM_PROVIDER == "mock":
        console.print(
            Panel(
                "[yellow]未检测到 LLM API Key！[/yellow]\n\n"
                "请在项目根目录创建 .env 文件并配置：\n"
                "  DEEPSEEK_API_KEY=your_key    (推荐)\n"
                "  或 DASHSCOPE_API_KEY=your_key (通义千问)\n\n"
                "可参考 .env.example 文件。",
                title="配置提醒",
                border_style="yellow",
            )
        )
        sys.exit(1)

    # 打印配置和图结构
    print_config()
    print_graph_structure()

    # 构建图
    console.print("\n[dim]正在构建 Agent 图...[/dim]")
    graph = build_graph()
    console.print("[green]Agent 图构建成功！[/green]")

    # 交互循环
    while True:
        print_example_questions()

        user_input = Prompt.ask(
            "[bold]请输入故障描述或问题序号[/bold]",
            default="1",
        )

        # 处理序号输入
        if user_input.strip().isdigit():
            idx = int(user_input.strip())
            if 1 <= idx <= len(EXAMPLE_QUESTIONS):
                question = EXAMPLE_QUESTIONS[idx - 1]
            else:
                console.print(f"[red]无效序号，请输入 1-{len(EXAMPLE_QUESTIONS)}[/red]")
                continue
        else:
            question = user_input.strip()
            if not question:
                continue

        # 执行诊断
        run_diagnosis(graph, question)

        # 是否继续
        console.print()
        cont = Prompt.ask(
            "\n[bold]是否继续诊断？[/bold]",
            choices=["y", "n"],
            default="y",
        )
        if cont.lower() != "y":
            break

    console.print("\n[bold cyan]感谢使用 NIO Diagnosis Agent！[/bold cyan]")


if __name__ == "__main__":
    main()
