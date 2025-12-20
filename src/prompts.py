from __future__ import annotations

import json
from typing import Any, Dict, List, Mapping


def _bool_cn(v: Any) -> str:
    return "是" if bool(v) else "否"


def format_candidate(candidate: Mapping[str, Any], scenario: str) -> str:
    """
    把结构化候选面料转成适合 LLM 阅读的短文本。
    """

    cid = candidate.get("id", "")
    cost = candidate.get("cost_level")
    lead = candidate.get("lead_time_level")

    compliance = candidate.get("compliance") or {}
    pfas_free = _bool_cn(compliance.get("pfas_free"))

    lines: List[str] = [f"id: {cid}", f"cost_level(1低-5高): {cost}", f"lead_time_level(1短-5长): {lead}", f"PFAS-free: {pfas_free}"]

    if scenario == "outdoor_dwr_windbreaker":
        lines.extend(
            [
                f"fabric_type: {candidate.get('fabric_type')}",
                f"finish: {candidate.get('finish')}",
                f"weight_gsm: {candidate.get('weight_gsm')}",
                f"water_repellency(1-5): {candidate.get('water_repellency')}",
                f"breathability(1-5): {candidate.get('breathability')}",
                f"abrasion(1-5): {candidate.get('abrasion')}",
                f"handfeel_noise(1-5,越高越安静/手感好): {candidate.get('handfeel_noise')}",
            ]
        )
    elif scenario == "winter_warm_midlayer":
        care = candidate.get("care") or {}
        lines.extend(
            [
                f"material_type: {candidate.get('material_type')}",
                f"loft_or_clo: {candidate.get('loft_or_clo')}",
                f"wind_blocking(1-5): {candidate.get('wind_blocking')}",
                f"moisture_management(1-5): {candidate.get('moisture_management')}",
                f"bulk_weight(1轻薄-5臃肿/重): {candidate.get('bulk_weight')}",
                f"machine_wash: {_bool_cn(care.get('machine_wash'))}",
            ]
        )
    else:
        # fallback：直接 dump
        lines.append("raw_json: " + json.dumps(candidate, ensure_ascii=False))

    return "\n".join(lines)


def format_options(options: Mapping[str, Mapping[str, Any]], scenario: str) -> str:
    blocks = []
    for k in ["A", "B", "C", "D"]:
        c = options[k]
        blocks.append(f"【{k}】\n{format_candidate(c, scenario)}")
    return "\n\n".join(blocks)


def system_prompt_general() -> str:
    return (
        "你是资深服装面料/材料决策助手。你会严格按硬约束 must 先淘汰，再按软偏好 prefer 综合权衡。\n"
        "重要：最终必须给出且只给出一个选项字母 A/B/C/D。"
    )


def user_prompt_mcq(stem: str, options: Mapping[str, Mapping[str, Any]], scenario: str) -> str:
    return (
        stem
        + "\n\n候选面料如下：\n"
        + format_options(options, scenario)
        + "\n\n请在最后一行输出：FINAL: X（X 为 A/B/C/D 之一）。"
    )


def few_shot_examples() -> List[Dict[str, str]]:
    """
    极简 few-shot：每个场景 1 个示例，控制 token 成本。
    """

    ex_outdoor_user = (
        "任务：为“户外轻量防泼风衣”选择面料。硬约束：PFAS-free；拒水>=4/5；耐磨>=3/5。"
        "软偏好：拒水/透气/耐磨/噪音手感/轻量/成本/交期。\n\n"
        "【A】water_repellency=5, breathability=4, abrasion=4, handfeel_noise=4, weight_gsm=95, cost_level=3, lead_time_level=2, PFAS-free=是\n"
        "【B】water_repellency=3, breathability=5, abrasion=4, handfeel_noise=4, weight_gsm=90, cost_level=2, lead_time_level=2, PFAS-free=是\n"
        "【C】water_repellency=4, breathability=3, abrasion=3, handfeel_noise=3, weight_gsm=120, cost_level=5, lead_time_level=4, PFAS-free=是\n"
        "【D】water_repellency=4, breathability=4, abrasion=3, handfeel_noise=2, weight_gsm=110, cost_level=3, lead_time_level=3, PFAS-free=否\n\n"
        "最终答案字母？"
    )
    ex_outdoor_assistant = "FINAL: A"

    ex_winter_user = (
        "任务：为“冬季保暖中层”选择材料方案。硬约束：可机洗；loft_or_clo>=1.2；排汗快干>=3/5。"
        "软偏好：保暖/抗风/排汗快干/轻薄/成本/交期。\n\n"
        "【A】loft_or_clo=1.9, wind_blocking=3, moisture_management=4, bulk_weight=3, machine_wash=是, cost_level=4, lead_time_level=4\n"
        "【B】loft_or_clo=1.5, wind_blocking=4, moisture_management=4, bulk_weight=2, machine_wash=是, cost_level=3, lead_time_level=2\n"
        "【C】loft_or_clo=1.1, wind_blocking=5, moisture_management=4, bulk_weight=2, machine_wash=是, cost_level=2, lead_time_level=2\n"
        "【D】loft_or_clo=1.6, wind_blocking=2, moisture_management=2, bulk_weight=2, machine_wash=是, cost_level=2, lead_time_level=2\n\n"
        "最终答案字母？"
    )
    ex_winter_assistant = "FINAL: B"

    return [
        {"role": "user", "content": ex_outdoor_user},
        {"role": "assistant", "content": ex_outdoor_assistant},
        {"role": "user", "content": ex_winter_user},
        {"role": "assistant", "content": ex_winter_assistant},
    ]


def fashionprompt_template() -> str:
    """
    结构化决策模板（FASHIONPROMPT 风格）：强调 must -> prefer -> tie-break 的流程。
    """

    return (
        "请按以下结构完成决策（可简写，避免长篇）：\n"
        "【必须】第一行必须是：FINAL: X（X 为 A/B/C/D 之一）\n"
        "然后可选写三段（每段 1-3 行即可）：\n"
        "1) Must Check：逐项检查每个选项是否违反硬约束（若违反，标记 MUST-FAIL）。\n"
        "2) Prefer Scoring：对未 MUST-FAIL 的选项，用 0-5 分做简短对比（只挑 2-3 个最关键软指标）。\n"
        "3) Risk Notes：列出 1-3 条风险点。\n"
        "注意：不要复述题干/候选原文；总输出尽量控制在 150-250 字以内。\n"
    )


