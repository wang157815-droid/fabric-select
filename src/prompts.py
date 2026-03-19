from __future__ import annotations

import json
from typing import Any, Dict, List, Mapping


def _bool_label(v: Any) -> str:
    return "yes" if bool(v) else "no"


def format_candidate(candidate: Mapping[str, Any], scenario: str) -> str:
    """
    Convert a structured candidate record into short LLM-friendly text.
    """

    cid = candidate.get("id", "")
    cost = candidate.get("cost_level")
    lead = candidate.get("lead_time_level")

    compliance = candidate.get("compliance") or {}
    pfas_free = _bool_label(compliance.get("pfas_free"))

    lines: List[str] = [
        f"id: {cid}",
        f"cost_level(1=low, 5=high): {cost}",
        f"lead_time_level(1=short, 5=long): {lead}",
        f"PFAS-free: {pfas_free}",
    ]

    if scenario == "outdoor_dwr_windbreaker":
        lines.extend(
            [
                f"fabric_type: {candidate.get('fabric_type')}",
                f"finish: {candidate.get('finish')}",
                f"weight_gsm: {candidate.get('weight_gsm')}",
                f"water_repellency(1-5): {candidate.get('water_repellency')}",
                f"breathability(1-5): {candidate.get('breathability')}",
                f"abrasion(1-5): {candidate.get('abrasion')}",
                f"handfeel_noise(1-5, higher=quieter/better handfeel): {candidate.get('handfeel_noise')}",
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
                f"bulk_weight(1=light/thin, 5=bulky/heavy): {candidate.get('bulk_weight')}",
                f"machine_wash: {_bool_label(care.get('machine_wash'))}",
            ]
        )
    else:
        # Fallback: dump the raw JSON directly.
        lines.append("raw_json: " + json.dumps(candidate, ensure_ascii=False))

    return "\n".join(lines)


def format_options(options: Mapping[str, Mapping[str, Any]], scenario: str) -> str:
    blocks = []
    for k in ["A", "B", "C", "D"]:
        c = options[k]
        blocks.append(f"[{k}]\n{format_candidate(c, scenario)}")
    return "\n\n".join(blocks)


def system_prompt_general() -> str:
    return (
        "You are an experienced apparel fabric/material decision assistant. "
        "Strictly eliminate options that violate hard constraints (`must`) "
        "before trading off soft preferences (`prefer`).\n"
        "Important: the final answer must be exactly one option letter: A/B/C/D."
    )


def user_prompt_mcq(stem: str, options: Mapping[str, Mapping[str, Any]], scenario: str) -> str:
    return (
        stem
        + "\n\nCandidate fabrics:\n"
        + format_options(options, scenario)
        + "\n\nOn the final line, output: FINAL: X (where X is one of A/B/C/D)."
    )


def few_shot_examples() -> List[Dict[str, str]]:
    """
    Minimal few-shot setup: one example per scenario to keep token cost low.
    """

    ex_outdoor_user = (
        "Task: select a fabric for a lightweight outdoor DWR windbreaker. "
        "Hard constraints: PFAS-free; water_repellency>=4/5; abrasion>=3/5. "
        "Soft preferences: water repellency / breathability / abrasion / "
        "quiet handfeel / light weight / cost / lead time.\n\n"
        "[A] water_repellency=5, breathability=4, abrasion=4, handfeel_noise=4, weight_gsm=95, cost_level=3, lead_time_level=2, PFAS-free=yes\n"
        "[B] water_repellency=3, breathability=5, abrasion=4, handfeel_noise=4, weight_gsm=90, cost_level=2, lead_time_level=2, PFAS-free=yes\n"
        "[C] water_repellency=4, breathability=3, abrasion=3, handfeel_noise=3, weight_gsm=120, cost_level=5, lead_time_level=4, PFAS-free=yes\n"
        "[D] water_repellency=4, breathability=4, abrasion=3, handfeel_noise=2, weight_gsm=110, cost_level=3, lead_time_level=3, PFAS-free=no\n\n"
        "Final answer letter?"
    )
    ex_outdoor_assistant = "FINAL: A"

    ex_winter_user = (
        "Task: select a material option for a winter warm midlayer. "
        "Hard constraints: machine washable; loft_or_clo>=1.2; "
        "moisture_management>=3/5. Soft preferences: warmth / wind blocking / "
        "moisture management / low bulk / cost / lead time.\n\n"
        "[A] loft_or_clo=1.9, wind_blocking=3, moisture_management=4, bulk_weight=3, machine_wash=yes, cost_level=4, lead_time_level=4\n"
        "[B] loft_or_clo=1.5, wind_blocking=4, moisture_management=4, bulk_weight=2, machine_wash=yes, cost_level=3, lead_time_level=2\n"
        "[C] loft_or_clo=1.1, wind_blocking=5, moisture_management=4, bulk_weight=2, machine_wash=yes, cost_level=2, lead_time_level=2\n"
        "[D] loft_or_clo=1.6, wind_blocking=2, moisture_management=2, bulk_weight=2, machine_wash=yes, cost_level=2, lead_time_level=2\n\n"
        "Final answer letter?"
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
    Structured decision template in a FASHIONPROMPT-like style.
    """

    return (
        "Use the following structure for the decision (brief wording is fine; avoid long explanations):\n"
        "[Required] The first line must be: FINAL: X (where X is one of A/B/C/D)\n"
        "You may then optionally add three short sections (1-3 lines each):\n"
        "1) Must Check: check each option against the hard constraints and mark violations as MUST-FAIL.\n"
        "2) Prefer Scoring: compare the non-MUST-FAIL options on a 0-5 scale, focusing on only 2-3 key soft criteria.\n"
        "3) Risk Notes: list 1-3 risks.\n"
        "Do not restate the full prompt or candidate text; keep the total response roughly within 150-250 words.\n"
    )


