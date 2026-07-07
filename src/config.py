"""
配置管理模块 - 集中管理 LLM、向量库、数据路径等配置
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# ============================================
# 路径配置
# ============================================
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
VECTOR_STORE_DIR = PROJECT_ROOT / "vector_store"

# 数据文件路径
TEST_REPORTS_PATH = DATA_DIR / "test_reports.json"
ANOMALY_LOGS_PATH = DATA_DIR / "anomaly_logs.json"
HISTORICAL_CASES_PATH = DATA_DIR / "historical_cases.csv"
BUSINESS_SCHEMA_PATH = DATA_DIR / "business_schema.json"

# ============================================
# LLM 配置
# ============================================
# 供应商优先级：openai > deepseek > tongyi > mock
# openai 模式支持任意 OpenAI 兼容 API（如阿里内部路由、vLLM、Ollama 等）
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")

# LLM 模型选择：优先级 openai > deepseek > tongyi > mock
if OPENAI_API_KEY and OPENAI_BASE_URL:
    LLM_PROVIDER = "openai"
elif DEEPSEEK_API_KEY:
    LLM_PROVIDER = "deepseek"
elif DASHSCOPE_API_KEY:
    LLM_PROVIDER = "tongyi"
else:
    LLM_PROVIDER = "mock"

# 模型名称
DEEPSEEK_MODEL = "deepseek-chat"          # DeepSeek V3
DEEPSEEK_EMBEDDING_MODEL = "text-embedding-v1"  # DeepSeek 暂不提供 embedding，使用社区方案
TONGYI_MODEL = "qwen-plus"
TONGYI_EMBEDDING_MODEL = "text-embedding-v2"

# 当前使用的 LLM 模型名（用于打印配置）
CURRENT_LLM_MODEL = {
    "openai": OPENAI_MODEL,
    "deepseek": DEEPSEEK_MODEL,
    "tongyi": TONGYI_MODEL,
}.get(LLM_PROVIDER, "N/A")

# Embedding 供应商
# 可通过环境变量 EMBEDDING_PROVIDER 显式覆盖（openai / tongyi / huggingface）
# OpenAI 兼容端点可能不支持 embedding，如遇报错请设为 huggingface
_EMBEDDING_OVERRIDE = os.getenv("EMBEDDING_PROVIDER", "")
if _EMBEDDING_OVERRIDE:
    EMBEDDING_PROVIDER = _EMBEDDING_OVERRIDE
elif OPENAI_API_KEY and OPENAI_BASE_URL:
    EMBEDDING_PROVIDER = "openai"
elif DASHSCOPE_API_KEY:
    EMBEDDING_PROVIDER = "tongyi"
else:
    EMBEDDING_PROVIDER = "huggingface"

# ============================================
# Agent 配置
# ============================================
MAX_RETRY_COUNT = 3          # 问题改写最大重试次数
RETRIEVAL_TOP_K = 4          # 向量检索返回文档数
CHUNK_SIZE = 500             # 文档分割块大小
CHUNK_OVERLAP = 50           # 文档分割重叠大小

# ============================================
# 向量库配置
# ============================================
FAISS_INDEX_PATH = str(VECTOR_STORE_DIR / "faiss_index")


def get_llm():
    """获取 LLM 实例，根据配置自动选择供应商"""
    if LLM_PROVIDER == "openai":
        # 支持任意 OpenAI 兼容 API：阿里内部路由、vLLM、Ollama、Together AI 等
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=OPENAI_MODEL,
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_BASE_URL,
            temperature=0,
            max_tokens=4096,
        )
    elif LLM_PROVIDER == "deepseek":
        from langchain_deepseek import ChatDeepSeek
        return ChatDeepSeek(
            model=DEEPSEEK_MODEL,
            api_key=DEEPSEEK_API_KEY,
            temperature=0,
            max_tokens=2048,
        )
    elif LLM_PROVIDER == "tongyi":
        from langchain_tongyi import ChatTongyi
        return ChatTongyi(
            model=TONGYI_MODEL,
            api_key=DASHSCOPE_API_KEY,
            temperature=0,
        )
    else:
        raise ValueError(
            "未检测到 LLM API Key，请在 .env 中配置：\n"
            "  方式1（OpenAI 兼容 API）：OPENAI_API_KEY + OPENAI_BASE_URL + OPENAI_MODEL\n"
            "  方式2（DeepSeek）：DEEPSEEK_API_KEY\n"
            "  方式3（通义千问）：DASHSCOPE_API_KEY"
        )


def get_embeddings():
    """获取 Embeddings 实例"""
    if EMBEDDING_PROVIDER == "openai":
        # 尝试使用 OpenAI 兼容端点的 embedding
        # 如果端点不支持 embedding，会抛异常，调用方可降级为 HuggingFace
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_BASE_URL,
        )
    elif EMBEDDING_PROVIDER == "tongyi":
        from langchain_community.embeddings import DashScopeEmbeddings
        return DashScopeEmbeddings(
            model=TONGYI_EMBEDDING_MODEL,
            dashscope_api_key=DASHSCOPE_API_KEY,
        )
    else:
        # 使用 HuggingFace 本地 embedding 模型，无需 API Key
        from langchain_huggingface import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        )


def print_config():
    """打印当前配置信息"""
    from rich.console import Console
    from rich.table import Table

    console = Console()
    table = Table(title="NIO Diagnosis Agent 配置", show_header=True)
    table.add_column("配置项", style="cyan")
    table.add_column("值", style="green")

    table.add_row("LLM 供应商", LLM_PROVIDER)
    table.add_row("LLM 模型", CURRENT_LLM_MODEL)
    if LLM_PROVIDER == "openai":
        table.add_row("API Base URL", OPENAI_BASE_URL)
    table.add_row("Embedding 供应商", EMBEDDING_PROVIDER)
    table.add_row("最大重试次数", str(MAX_RETRY_COUNT))
    table.add_row("检索 Top-K", str(RETRIEVAL_TOP_K))
    table.add_row("数据目录", str(DATA_DIR))

    console.print(table)
