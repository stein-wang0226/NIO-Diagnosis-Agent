"""
规则校验工具 - 基于 Business Schema 进行业务规则校验

从 business_schema.json 加载错误码映射、组件依赖关系和校验规则，
对诊断信息进行结构化校验，输出校验结果。
"""

import json
from langchain.tools import tool

from src.config import BUSINESS_SCHEMA_PATH


def _load_schema() -> dict:
    """加载业务 Schema"""
    with open(str(BUSINESS_SCHEMA_PATH), "r", encoding="utf-8") as f:
        return json.load(f)


@tool
def validate_rules(error_code: str) -> str:
    """
    根据错误码从业务 Schema 中查询校验规则并返回校验结果。
    输入错误码（如 BMS_CHG_TIMEOUT_003），
    返回该错误码对应的组件信息、阈值定义、严重度和相关错误码，
    以及适用的校验规则。
    """
    schema = _load_schema()

    # 查询错误码映射
    code_mappings = schema.get("error_code_mappings", {})
    code_info = code_mappings.get(error_code, {})

    if not code_info:
        # 模糊匹配
        for code, info in code_mappings.items():
            if error_code.lower() in code.lower() or code.lower() in error_code.lower():
                code_info = info
                error_code = code
                break

    if not code_info:
        return f"未找到错误码 {error_code} 对应的业务规则。"

    # 查询相关校验规则
    validation_rules = schema.get("validation_rules", [])
    applicable_rules = [
        rule for rule in validation_rules
        if error_code in rule.get("applies_to", [])
    ]

    # 查询组件依赖
    component = code_info.get("component", "")
    component_deps = schema.get("component_dependencies", {}).get(component, {})

    # 查询相关错误码信息
    related_codes = code_info.get("related_error_codes", [])
    related_info = []
    for rc in related_codes:
        rc_info = code_mappings.get(rc, {})
        if rc_info:
            related_info.append(f"  - {rc}: {rc_info.get('description', '')} [严重度: {rc_info.get('severity', '')}]")

    # 查询术语
    glossary = schema.get("terminology_glossary", {})
    component_abbr = component.split(".")[0] if component else ""
    term_def = glossary.get(component_abbr, "")

    result = (
        f"=== 业务规则校验结果 ===\n"
        f"错误码: {error_code}\n"
        f"组件: {component}"
        + (f"（{term_def}）" if term_def else "")
        + "\n"
        f"描述: {code_info.get('description', 'N/A')}\n"
        f"阈值: {code_info.get('threshold', 'N/A')}\n"
        f"严重度: {code_info.get('severity', 'N/A')}\n"
        f"\n--- 关联错误码 ---\n"
        + ("\n".join(related_info) if related_info else "  无")
        + "\n"
        f"\n--- 适用校验规则 ---\n"
    )

    if applicable_rules:
        for rule in applicable_rules:
            result += (
                f"  规则ID: {rule['rule_id']}\n"
                f"  名称: {rule['name']}\n"
                f"  描述: {rule['description']}\n"
                f"  逻辑: {rule['logic']}\n\n"
            )
    else:
        result += "  无特定校验规则\n"

    result += (
        f"--- 组件依赖 ---\n"
        f"  依赖组件: {component_deps.get('depends_on', 'N/A')}\n"
        f"  说明: {component_deps.get('description', 'N/A')}\n"
    )

    return result
