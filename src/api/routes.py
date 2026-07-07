"""
API 路由 - 提供 SSE 流式诊断端点和配置端点

后端核心代码零改动，仅在此层包装 graph.stream() 为 SSE 事件流。
"""

import json

from fastapi import APIRouter
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from src.config import (
    LLM_PROVIDER,
    CURRENT_LLM_MODEL,
    EMBEDDING_PROVIDER,
    MAX_RETRY_COUNT,
)
from src.graph import get_graph

router = APIRouter()

# 示例问题（与 main.py 保持一致）
EXAMPLE_QUESTIONS = [
    "BMS 充电握手超时，CML 报文延迟 12s，帮我分析原因",
    "AEB 在强光环境下没有触发制动，置信度只有 0.72，怎么回事？",
    "NOMI 多轮对话上下文丢失，第3轮对话找不到导航目的地",
    "OTA 断点续传失败，下载到 60% 中断后从头开始下载",
    "LKA 弯道居中偏移 0.35m 超出阈值，R250m 弯道处",
    "BMS 高温降温延迟，液冷泵 15s 才启动",
]

# 节点中文标签映射
NODE_LABELS = {
    "log_fetch": "日志获取",
    "retrieve": "知识检索",
    "grade": "文档评分",
    "rewrite": "问题改写",
    "rule_check": "规则校验",
    "analyze": "原因分析",
}


class DiagnosisRequest(BaseModel):
    """诊断请求体"""
    question: str


def _make_initial_state(question: str) -> dict:
    """构建初始状态（与 main.py 中的 initial_state 逻辑一致）"""
    return {
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


def _serialize_state_fields(fields: dict) -> dict:
    """序列化状态字段，过滤掉 messages（体积大且前端不需要）"""
    return {k: v for k, v in fields.items() if k != "messages"}


@router.get("/health")
async def health_check() -> dict:
    """健康检查端点"""
    return {"status": "ok", "llm_provider": LLM_PROVIDER}


@router.get("/config")
async def get_config() -> dict:
    """返回当前 Agent 配置信息"""
    return {
        "llm_provider": LLM_PROVIDER,
        "llm_model": CURRENT_LLM_MODEL,
        "embedding_provider": EMBEDDING_PROVIDER,
        "max_retry_count": MAX_RETRY_COUNT,
        "examples": EXAMPLE_QUESTIONS,
        "node_labels": NODE_LABELS,
    }


@router.get("/examples")
async def get_examples() -> dict:
    """返回示例问题列表"""
    return {"examples": EXAMPLE_QUESTIONS}


@router.post("/diagnose")
async def diagnose(request: DiagnosisRequest):
    """
    核心端点：执行诊断流程，返回 SSE 流。

    使用 graph.stream() 获取每个节点执行后的状态更新，
    通过 Server-Sent Events 实时推送到前端。

    SSE 事件类型：
    - node_update: 节点执行完成，携带节点名和状态更新
    - done: 全部流程结束，携带最终状态
    - error: 执行出错，携带错误信息
    """

    def event_generator():
        initial_state = _make_initial_state(request.question)
        accumulated_state = dict(initial_state)

        try:
            graph = get_graph()

            for update in graph.stream(
                initial_state,
                {"recursion_limit": 25},
                stream_mode="updates",
            ):
                # LangGraph updates 模式: {node_name: {field: value, ...}}
                for node_name, state_update in update.items():
                    # 跳过内部事件（如 __start__, __end__）
                    if node_name.startswith("__"):
                        continue

                    # 累积状态
                    for k, v in state_update.items():
                        if k == "messages":
                            accumulated_state[k] = accumulated_state.get(k, []) + v
                        else:
                            accumulated_state[k] = v

                    yield {
                        "event": "node_update",
                        "data": json.dumps(
                            {
                                "node": node_name,
                                "label": NODE_LABELS.get(node_name, node_name),
                                "fields": _serialize_state_fields(state_update),
                                "retry_count": accumulated_state.get("retry_count", 0),
                                "is_relevant": accumulated_state.get("is_relevant", False),
                            },
                            ensure_ascii=False,
                        ),
                    }

            # 最终事件：携带完整最终状态
            yield {
                "event": "done",
                "data": json.dumps(
                    {
                        "diagnosis_report": accumulated_state.get("diagnosis_report", ""),
                        "retry_count": accumulated_state.get("retry_count", 0),
                        "is_relevant": accumulated_state.get("is_relevant", False),
                        "log_data_len": len(accumulated_state.get("log_data", "")),
                        "retrieved_docs_len": len(accumulated_state.get("retrieved_docs", "")),
                        "rule_check_result_len": len(accumulated_state.get("rule_check_result", "")),
                    },
                    ensure_ascii=False,
                ),
            }

        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps(
                    {"error": f"诊断过程出错: {str(e)}"},
                    ensure_ascii=False,
                ),
            }

    return EventSourceResponse(event_generator())
