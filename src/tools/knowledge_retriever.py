"""
知识检索工具 - 基于 LangChain RAG 从历史案例库中检索相似故障案例

使用 LangChain 的 CSVLoader 加载历史案例，通过 Embeddings 向量化后存入 FAISS，
封装为 @tool 供 LangGraph 节点调用。
"""

import json
from pathlib import Path
from functools import lru_cache

from langchain.tools import tool
from langchain_community.document_loaders import CSVLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from src.config import (
    HISTORICAL_CASES_PATH,
    BUSINESS_SCHEMA_PATH,
    FAISS_INDEX_PATH,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    RETRIEVAL_TOP_K,
    get_embeddings,
)


def _build_vectorstore() -> FAISS:
    """构建 FAISS 向量库：加载历史案例 CSV -> 分割 -> 向量化"""
    # 加载历史案例
    loader = CSVLoader(file_path=str(HISTORICAL_CASES_PATH))
    documents = loader.load()

    # 为每个文档增加元数据：加载业务术语表作为上下文
    terminology = _load_terminology()
    for doc in documents:
        doc.metadata["source"] = "historical_cases"
        # 在文档内容前添加术语表，帮助 embedding 理解专业术语
        doc.page_content = f"[术语参考] {terminology}\n\n{doc.page_content}"

    # 分割文档
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n", "。", "；", "，", " ", ""],
    )
    splits = text_splitter.split_documents(documents)

    # 创建向量库
    embeddings = get_embeddings()
    vectorstore = FAISS.from_documents(splits, embeddings)

    # 持久化到本地
    vectorstore.save_local(FAISS_INDEX_PATH)
    return vectorstore


def _load_terminology() -> str:
    """加载业务术语表"""
    with open(BUSINESS_SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = json.load(f)
    glossary = schema.get("terminology_glossary", {})
    return "; ".join([f"{k}={v}" for k, v in glossary.items()])


@lru_cache(maxsize=1)
def _get_vectorstore() -> FAISS:
    """获取向量库实例（优先加载本地缓存，不存在则重建）"""
    index_path = Path(FAISS_INDEX_PATH)
    if index_path.exists():
        embeddings = get_embeddings()
        return FAISS.load_local(
            FAISS_INDEX_PATH,
            embeddings,
            allow_dangerous_deserialization=True,
        )
    return _build_vectorstore()


@tool
def retrieve_cases(query: str) -> str:
    """
    从历史故障案例知识库中检索与问题相关的案例。
    输入用户关于故障/异常的自然语言描述，
    返回最相关的历史案例信息（含根因、排查过程、解决方案）。
    """
    vectorstore = _get_vectorstore()
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": RETRIEVAL_TOP_K},
    )
    docs = retriever.invoke(query)

    if not docs:
        return "未检索到相关历史案例。"

    results = []
    for i, doc in enumerate(docs, 1):
        results.append(f"--- 相似案例 {i} ---\n{doc.page_content}\n")

    return "\n".join(results)


@tool
def fetch_test_data(query: str) -> str:
    """
    从测试报告数据库中检索与问题相关的测试报告。
    输入关于测试用例、测试结果或异常描述的自然语言查询，
    返回匹配的测试报告信息（含用例ID、测试结果、异常信息等）。
    """
    from src.config import TEST_REPORTS_PATH
    with open(str(TEST_REPORTS_PATH), "r", encoding="utf-8") as f:
        reports = json.load(f)

    # 简单关键词匹配（Demo 用，实际场景可换为向量检索）
    query_lower = query.lower()
    matched = []
    for report in reports:
        searchable = " ".join(str(v) for v in report.values()).lower()
        if any(kw in searchable for kw in query_lower.split()):
            matched.append(report)

    if not matched:
        matched = reports[:3]  # 默认返回前3条

    results = []
    for r in matched:
        results.append(
            f"用例ID: {r['case_id']} | 结果: {r['test_result']} | 严重度: {r['severity']}\n"
            f"测试套: {r['test_suite']} | 车型: {r['vehicle_model']} | 版本: {r['software_version']}\n"
            f"错误信息: {r['error_message'] or 'N/A'}\n"
            f"期望: {r['expected_behavior']}\n"
            f"实际: {r['actual_behavior']}\n"
        )

    return "\n---\n".join(results)
