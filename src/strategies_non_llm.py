from __future__ import annotations

import json
import random
import zlib
from typing import Any, Dict, List, Mapping, Optional

from .scoring import check_must

OptionKey = str  # "A"/"B"/"C"/"D"

NON_LLM_STRATEGIES = {"nonllm_feasible_random", "nonllm_simple_heuristic"}


def _reason_to_must_cond_map() -> Dict[str, Dict[str, Any]]:
    """
    将题目 meta.must_sample（中文 reason 文本）映射回 must 条件配置。
    这些模板来自数据生成脚本 `dataset_v1.py`，保证与题目一致。
    """
    # 延迟导入，避免不必要的重 import 成本
    from . import dataset_v1 as dv1  # local import

    m: Dict[str, Dict[str, Any]] = {}
    for cond in list(getattr(dv1, "MUST_TEMPLATES_OUTDOOR", [])) + list(getattr(dv1, "MUST_TEMPLATES_WINTER", [])):
        reason = str(cond.get("reason") or "").strip()
        if reason:
            m[reason] = dict(cond)
    return m


_REASON_TO_COND = _reason_to_must_cond_map()


def _build_rules_from_question(question: Mapping[str, Any]) -> Dict[str, Any]:
    must_reasons = question.get("meta", {}).get("must_sample", []) or []
    must_list: List[Dict[str, Any]] = []
    for r in must_reasons:
        cond = _REASON_TO_COND.get(str(r))
        if cond:
            must_list.append(cond)
    return {"must": must_list}


def _feasible_keys(question: Mapping[str, Any]) -> List[OptionKey]:
    rules = _build_rules_from_question(question)
    ok: List[OptionKey] = []
    options = question.get("options") or {}
    for k, opt in options.items():
        kk = str(k).strip()
        if kk not in ("A", "B", "C", "D"):
            continue
        ok_flag, _ = check_must(opt, rules)
        if ok_flag:
            ok.append(kk)
    return ok


def _stable_seed(question_id: str) -> int:
    # Python hash 会随进程随机化；这里用 crc32 保证跨进程稳定
    return int(zlib.crc32(question_id.encode("utf-8"))) & 0x7FFFFFFF


def _pick_feasible_random(question: Mapping[str, Any], *, rng: random.Random) -> OptionKey:
    feasible = _feasible_keys(question)
    keys = feasible if feasible else ["A", "B", "C", "D"]
    return str(rng.choice(keys))


def _pick_simple_heuristic(question: Mapping[str, Any]) -> OptionKey:
    """
    非LLM朴素启发式（不使用 oracle_scores，也不复刻完整 prefer 权重）。
    逻辑：先 must 过滤，再用少量关键字段做字典序排序。
    """
    scenario = str(question.get("scenario") or "")
    feasible = _feasible_keys(question)
    keys = feasible if feasible else ["A", "B", "C", "D"]

    options = question.get("options") or {}

    def _int(v: Any, default: int = 0) -> int:
        try:
            return int(v)
        except Exception:
            return default

    def _float(v: Any, default: float = 0.0) -> float:
        try:
            return float(v)
        except Exception:
            return default

    if scenario == "outdoor_dwr_windbreaker":

        def score(k: OptionKey) -> tuple:
            o = options.get(k) or {}
            return (
                _int(o.get("water_repellency")),  # high better
                _int(o.get("breathability")),  # high better
                _int(o.get("abrasion")),  # high better
                _int(o.get("handfeel_noise")),  # high better（按数据集定义）
                -_float(o.get("weight_gsm"), default=1e9),  # low better
                -_int(o.get("cost_level"), default=999),  # low better
                -_int(o.get("lead_time_level"), default=999),  # low better
                -ord(str(k)),  # tie-break: prefer A > B > C > D
            )

        return max(keys, key=score)

    # winter_warm_midlayer
    def score_w(k: OptionKey) -> tuple:
        o = options.get(k) or {}
        return (
            _float(o.get("loft_or_clo")),  # high better
            _int(o.get("moisture_management")),  # high better
            _int(o.get("wind_blocking")),  # high better
            -_int(o.get("bulk_weight"), default=999),  # low better
            -_int(o.get("cost_level"), default=999),  # low better
            -_int(o.get("lead_time_level"), default=999),  # low better
            -ord(str(k)),
        )

    return max(keys, key=score_w)


def run_non_llm_strategy(
    question: Mapping[str, Any],
    *,
    strategy: str,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    返回结构与 LLM 策略保持一致：
      - pick: A/B/C/D
      - calls: []
      - raw_output: 用 JSON 记录可复核信息（不占太大体积）
    """
    if strategy not in NON_LLM_STRATEGIES:
        raise ValueError(f"Unknown non-LLM strategy: {strategy}")

    qid = str(question.get("id") or "")
    rng = random.Random(int(seed) if seed is not None else _stable_seed(qid))

    if strategy == "nonllm_feasible_random":
        pick = _pick_feasible_random(question, rng=rng)
    else:
        pick = _pick_simple_heuristic(question)

    raw = json.dumps(
        {
            "strategy": strategy,
            "question_id": qid,
            "scenario": str(question.get("scenario") or ""),
            "pick": pick,
            "feasible": _feasible_keys(question),
        },
        ensure_ascii=False,
    )
    return {"pick": pick, "calls": [], "raw_output": raw}

