"""
NIO Diagnosis Agent - 基本集成测试

测试图的构建、工具调用、状态流转等核心功能。
注意：涉及 LLM 调用的测试需要配置 API Key，
纯工具测试无需 LLM。
"""

import json
import pytest
from pathlib import Path


# ============================================
# 数据文件完整性测试
# ============================================
class TestDataIntegrity:
    """测试 Mock 数据文件完整性"""

    def test_test_reports_exists(self):
        """测试报告文件存在且格式正确"""
        from src.config import TEST_REPORTS_PATH
        with open(str(TEST_REPORTS_PATH), "r", encoding="utf-8") as f:
            data = json.load(f)
        assert len(data) >= 5, "测试报告应至少有5条"
        for report in data:
            assert "case_id" in report
            assert "test_result" in report
            assert "error_message" in report

    def test_anomaly_logs_exists(self):
        """异常日志文件存在且格式正确"""
        from src.config import ANOMALY_LOGS_PATH
        with open(str(ANOMALY_LOGS_PATH), "r", encoding="utf-8") as f:
            data = json.load(f)
        assert len(data) >= 5, "异常日志应至少有5条"
        for log in data:
            assert "log_id" in log
            assert "level" in log
            assert "error_code" in log
            assert "component" in log

    def test_historical_cases_exists(self):
        """历史案例 CSV 文件存在"""
        from src.config import HISTORICAL_CASES_PATH
        assert HISTORICAL_CASES_PATH.exists(), "historical_cases.csv 不存在"
        content = HISTORICAL_CASES_PATH.read_text(encoding="utf-8")
        assert "case_id" in content, "CSV 缺少 case_id 列"
        assert "root_cause" in content, "CSV 缺少 root_cause 列"

    def test_business_schema_exists(self):
        """业务 Schema 文件存在且结构正确"""
        from src.config import BUSINESS_SCHEMA_PATH
        with open(str(BUSINESS_SCHEMA_PATH), "r", encoding="utf-8") as f:
            schema = json.load(f)
        assert "error_code_mappings" in schema
        assert "component_dependencies" in schema
        assert "validation_rules" in schema
        assert "terminology_glossary" in schema
        assert len(schema["error_code_mappings"]) >= 10, "错误码映射应至少有10条"


# ============================================
# 工具测试（无需 LLM）
# ============================================
class TestTools:
    """测试 Agent 工具（不依赖 LLM）"""

    def test_fetch_logs(self):
        """测试日志获取工具"""
        from src.tools.log_fetcher import fetch_logs
        result = fetch_logs.invoke({"query": "BMS charging timeout"})
        assert isinstance(result, str)
        assert len(result) > 0, "日志获取结果不应为空"
        assert "BMS" in result or "ERROR" in result

    def test_fetch_logs_empty_query(self):
        """测试空查询返回默认日志"""
        from src.tools.log_fetcher import fetch_logs
        result = fetch_logs.invoke({"query": ""})
        assert isinstance(result, str)
        # 空查询应返回所有 ERROR 级别日志
        assert "ERROR" in result

    def test_validate_rules(self):
        """测试规则校验工具"""
        from src.tools.rule_validator import validate_rules
        result = validate_rules.invoke({"error_code": "BMS_CHG_TIMEOUT_003"})
        assert "BMS_CHG_TIMEOUT_003" in result
        assert "BMS.ChargingController" in result
        assert "严重度" in result

    def test_validate_rules_unknown_code(self):
        """测试未知错误码"""
        from src.tools.rule_validator import validate_rules
        result = validate_rules.invoke({"error_code": "UNKNOWN_001"})
        assert "未找到" in result

    def test_validate_rules_fuzzy_match(self):
        """测试模糊匹配"""
        from src.tools.rule_validator import validate_rules
        result = validate_rules.invoke({"error_code": "BMS_CHG_TIMEOUT"})
        assert "BMS_CHG_TIMEOUT_003" in result


# ============================================
# 图结构测试（无需 LLM）
# ============================================
class TestGraphStructure:
    """测试 LangGraph 图结构"""

    def test_graph_builds(self):
        """测试图可以成功构建"""
        from src.graph import build_graph
        graph = build_graph()
        assert graph is not None

    def test_graph_has_nodes(self):
        """测试图包含所有必需节点"""
        from src.graph import build_graph
        graph = build_graph()
        # 获取图中所有节点名
        node_names = set(graph.get_graph().nodes.keys())
        expected_nodes = {"log_fetch", "retrieve", "grade", "rewrite", "rule_check", "analyze"}
        assert expected_nodes.issubset(node_names), \
            f"图缺少节点，期望: {expected_nodes}, 实际: {node_names}"

    def test_graph_has_edges(self):
        """测试图包含必需的边"""
        from src.graph import build_graph
        graph = build_graph()
        graph_data = graph.get_graph()
        # 图应有边
        assert len(graph_data.edges) > 0, "图应至少有一条边"


# ============================================
# 节点单元测试（无需 LLM）
# ============================================
class TestNodes:
    """测试单个节点（不依赖 LLM 的节点）"""

    def test_log_fetch_node(self):
        """测试日志获取节点"""
        from src.nodes.log_fetch_node import log_fetch_node
        state = {"question": "BMS 充电超时", "messages": []}
        result = log_fetch_node(state)
        assert "log_data" in result
        assert len(result["log_data"]) > 0
        assert "messages" in result

    def test_rule_check_node(self):
        """测试规则校验节点"""
        from src.nodes.rule_check_node import rule_check_node
        state = {
            "log_data": "Error code: BMS_CHG_TIMEOUT_003 in log",
            "retrieved_docs": "AEB_CONF_LOW_002 detected",
        }
        result = rule_check_node(state)
        assert "rule_check_result" in result
        assert "BMS_CHG_TIMEOUT_003" in result["rule_check_result"]
        assert "AEB_CONF_LOW_002" in result["rule_check_result"]

    def test_rule_check_node_no_error_codes(self):
        """测试无错误码时的规则校验"""
        from src.nodes.rule_check_node import rule_check_node
        state = {
            "log_data": "some generic log without error codes",
            "retrieved_docs": "some test report without error codes",
        }
        result = rule_check_node(state)
        assert "rule_check_result" in result
        assert "未检测到" in result["rule_check_result"]


class TestGradeNode:
    """测试文档评分节点和路由函数"""

    def test_route_after_grading_relevant(self):
        """测试评分相关时的路由"""
        from src.nodes.grade_node import route_after_grading
        state = {"is_relevant": True, "retry_count": 0}
        assert route_after_grading(state) == "rule_check"

    def test_route_after_grading_not_relevant(self):
        """测试评分不相关时的路由"""
        from src.nodes.grade_node import route_after_grading
        state = {"is_relevant": False, "retry_count": 0}
        assert route_after_grading(state) == "rewrite"

    def test_route_after_grading_max_retry(self):
        """测试达到最大重试次数时的路由"""
        from src.nodes.grade_node import route_after_grading
        from src.config import MAX_RETRY_COUNT
        state = {"is_relevant": False, "retry_count": MAX_RETRY_COUNT}
        assert route_after_grading(state) == "rule_check"
