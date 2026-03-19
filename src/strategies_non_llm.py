from __future__ import annotations

import json
import random
import zlib
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple

from .scoring import check_must

OptionKey = str  # "A"/"B"/"C"/"D"

NON_LLM_STRATEGIES = {
    "nonllm_feasible_random",
    "nonllm_simple_heuristic",
    # stronger classical baselines (no LLM cost)
    "nonllm_topsis",
    "nonllm_vikor",
}

# Load scenario-level preference rules for MCDM baselines.
# These are deterministic and shared across all questions in a scenario.
_RULES_OUTDOOR = json.loads(Path("configs/rules_outdoor.json").read_text(encoding="utf-8"))
_RULES_WINTER = json.loads(Path("configs/rules_winter.json").read_text(encoding="utf-8"))


def _cond_key(cond: Mapping[str, Any]) -> Tuple[str, str, str]:
    return (
        str(cond.get("field")),
        str(cond.get("op", "eq")),
        json.dumps(cond.get("value"), ensure_ascii=False, sort_keys=True),
    )


def _u(s: str) -> str:
    return s.encode("ascii").decode("unicode_escape")


_LEGACY_REASON_ALIASES: Dict[Tuple[str, str, str], List[str]] = {
    ("compliance.pfas_free", "eq", "true"): [_u(r"\u5fc5\u987b PFAS-free\uff08\u5408\u89c4/\u53ef\u6301\u7eed\uff09")],
    ("water_repellency", "gte", "4"): [_u(r"\u62d2\u6c34/\u9632\u6cfc\u7b49\u7ea7\u81f3\u5c11 4/5")],
    ("water_repellency", "gte", "3"): [_u(r"\u62d2\u6c34/\u9632\u6cfc\u7b49\u7ea7\u81f3\u5c11 3/5")],
    ("abrasion", "gte", "3"): [_u(r"\u8010\u78e8\u7b49\u7ea7\u81f3\u5c11 3/5\uff08\u6237\u5916\u4f7f\u7528\u5f3a\u5ea6\uff09")],
    ("abrasion", "gte", "4"): [_u(r"\u8010\u78e8\u7b49\u7ea7\u81f3\u5c11 4/5\uff08\u9ad8\u5f3a\u5ea6\u6237\u5916\uff09")],
    ("breathability", "gte", "3"): [_u(r"\u900f\u6c14\u7b49\u7ea7\u81f3\u5c11 3/5")],
    ("weight_gsm", "lte", "120"): [_u(r"\u514b\u91cd\u4e0d\u8d85\u8fc7 120gsm\uff08\u8f7b\u91cf\u5316\uff09")],
    ("weight_gsm", "lte", "150"): [_u(r"\u514b\u91cd\u4e0d\u8d85\u8fc7 150gsm")],
    ("lead_time_level", "lte", "3"): [
        _u(r"\u4ea4\u671f\u7b49\u7ea7\u4e0d\u8d85\u8fc7 3\uff08\u5feb\u901f\u4e0a\u5e02\uff09"),
        _u(r"\u4ea4\u671f\u7b49\u7ea7\u4e0d\u8d85\u8fc7 3"),
    ],
    ("cost_level", "lte", "3"): [_u(r"\u6210\u672c\u7b49\u7ea7\u4e0d\u8d85\u8fc7 3\uff08\u9884\u7b97\u7ea6\u675f\uff09")],
    ("care.machine_wash", "eq", "true"): [_u(r"\u5fc5\u987b\u53ef\u673a\u6d17\uff08\u62a4\u7406\u7ea6\u675f\uff09")],
    ("loft_or_clo", "gte", "1.2"): [_u(r"\u4fdd\u6696\u6307\u6807\uff08loft/clo\uff09\u81f3\u5c11 1.2")],
    ("loft_or_clo", "gte", "1.5"): [_u(r"\u4fdd\u6696\u6307\u6807\uff08loft/clo\uff09\u81f3\u5c11 1.5\uff08\u9ad8\u4fdd\u6696\uff09")],
    ("moisture_management", "gte", "3"): [_u(r"\u6392\u6c57/\u5feb\u5e72\u80fd\u529b\u81f3\u5c11 3/5")],
    ("moisture_management", "gte", "4"): [_u(r"\u6392\u6c57/\u5feb\u5e72\u80fd\u529b\u81f3\u5c11 4/5\uff08\u9ad8\u8fd0\u52a8\u5f3a\u5ea6\uff09")],
    ("wind_blocking", "gte", "3"): [_u(r"\u6297\u98ce\u7b49\u7ea7\u81f3\u5c11 3/5")],
    ("bulk_weight", "lte", "3"): [_u(r"\u81c3\u80bf\u5ea6\u4e0d\u8d85\u8fc7 3\uff08\u8f7b\u8584\u8981\u6c42\uff09")],
    ("cost_level", "lte", "4"): [_u(r"\u6210\u672c\u7b49\u7ea7\u4e0d\u8d85\u8fc7 4")],
}


def _reason_to_must_cond_map() -> Dict[str, Dict[str, Any]]:
    """
    Map `question.meta.must_sample` reason text back to must-condition configs.

    These templates come from `dataset_v1.py` so the mapping stays consistent
    with generated questions.
    """
    # Delay the import to avoid unnecessary startup cost.
    from . import dataset_v1 as dv1  # local import

    m: Dict[str, Dict[str, Any]] = {}
    for cond in list(getattr(dv1, "MUST_TEMPLATES_OUTDOOR", [])) + list(getattr(dv1, "MUST_TEMPLATES_WINTER", [])):
        reason = str(cond.get("reason") or "").strip()
        if reason:
            m[reason] = dict(cond)
        for alias in _LEGACY_REASON_ALIASES.get(_cond_key(cond), []):
            m[str(alias).strip()] = dict(cond)
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
    # Python's built-in hash is process-randomized; crc32 is stable across runs.
    return int(zlib.crc32(question_id.encode("utf-8"))) & 0x7FFFFFFF


def _get_by_path(obj: Mapping[str, Any], path: str) -> Any:
    cur: Any = obj
    for part in str(path).split("."):
        if not isinstance(cur, Mapping) or part not in cur:
            return None
        cur = cur[part]
    return cur


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value)
    except Exception:
        return None


def _normalize(value: Any, normalization: Mapping[str, Any], direction: str) -> float:
    """
    Match src/scoring.py normalization semantics for prefer fields.
    Returns a utility in [0,1] where higher is better after applying direction.
    Missing -> 0.0 (worst-case).
    """
    if value is None:
        return 0.0
    ntype = str(normalization.get("type", "ordinal"))
    if ntype == "bool":
        v = 1.0 if bool(value) else 0.0
        return v if direction == "high" else 1.0 - v
    if ntype == "minmax":
        v = _to_float(value)
        vmin = _to_float(normalization.get("min"))
        vmax = _to_float(normalization.get("max"))
        if v is None or vmin is None or vmax is None:
            return 0.0
        if abs(vmax - vmin) < 1e-12:
            raw = 0.5
        else:
            raw = (v - vmin) / (vmax - vmin)
        raw = max(0.0, min(1.0, raw))
        return raw if direction == "high" else 1.0 - raw
    # ordinal fallback
    levels: List[Any] = list(normalization.get("levels", [])) or [1, 2, 3, 4, 5]
    try:
        idx = levels.index(value)
    except Exception:
        v = _to_float(value)
        lv = [_to_float(x) for x in levels]
        if v is None or any(x is None for x in lv):
            return 0.0
        idx = min(range(len(lv)), key=lambda i: abs(float(lv[i]) - float(v)))  # type: ignore[arg-type]
    denom = max(1, len(levels) - 1)
    raw = float(idx) / float(denom)
    return raw if direction == "high" else 1.0 - raw


def _topsis_pick(question: Mapping[str, Any]) -> Tuple[OptionKey, Dict[str, Any]]:
    scenario = str(question.get("scenario") or "")
    rules = _RULES_OUTDOOR if scenario == "outdoor_dwr_windbreaker" else _RULES_WINTER
    prefs = list(rules.get("prefer") or [])

    feasible = _feasible_keys(question)
    keys = feasible if feasible else ["A", "B", "C", "D"]
    options = question.get("options") or {}

    # utilities in [0,1], higher better
    crit_vals: Dict[OptionKey, List[float]] = {}
    # Use equal weights because the prompt does not expose numeric preference weights.
    weights: List[float] = [1.0 for _ in prefs]
    sw = float(len(weights)) or 1.0
    weights = [w / sw for w in weights]

    for k in keys:
        o = options.get(k) or {}
        vals = []
        for p in prefs:
            field = p.get("field")
            direction = str(p.get("direction", "high"))
            norm = p.get("normalization") or {"type": "ordinal", "levels": [1, 2, 3, 4, 5]}
            v = _get_by_path(o, str(field))
            vals.append(float(_normalize(v, norm, direction)))
        crit_vals[str(k)] = vals

    # vector normalization across alternatives (on 0..1 utilities)
    m = len(prefs)
    denom = [0.0] * m
    for j in range(m):
        denom[j] = sum((crit_vals[k][j] ** 2) for k in keys) ** 0.5
        if denom[j] <= 1e-12:
            denom[j] = 1.0

    # weighted normalized matrix
    vmat: Dict[OptionKey, List[float]] = {}
    for k in keys:
        vmat[k] = [(crit_vals[k][j] / denom[j]) * weights[j] for j in range(m)]

    ideal_best = [max(vmat[k][j] for k in keys) for j in range(m)]
    ideal_worst = [min(vmat[k][j] for k in keys) for j in range(m)]

    def dist(a: List[float], b: List[float]) -> float:
        return sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5

    scores: Dict[OptionKey, float] = {}
    for k in keys:
        d_pos = dist(vmat[k], ideal_best)
        d_neg = dist(vmat[k], ideal_worst)
        c = d_neg / (d_pos + d_neg) if (d_pos + d_neg) > 1e-12 else 0.0
        scores[k] = float(c)

    # deterministic tie-break: A > B > C > D
    pick = max(scores.keys(), key=lambda kk: (scores[kk], -ord(str(kk))))
    return str(pick), {"method": "topsis", "scores": scores, "feasible": keys, "weights": weights}


def _vikor_pick(question: Mapping[str, Any], v: float = 0.5) -> Tuple[OptionKey, Dict[str, Any]]:
    scenario = str(question.get("scenario") or "")
    rules = _RULES_OUTDOOR if scenario == "outdoor_dwr_windbreaker" else _RULES_WINTER
    prefs = list(rules.get("prefer") or [])

    feasible = _feasible_keys(question)
    keys = feasible if feasible else ["A", "B", "C", "D"]
    options = question.get("options") or {}

    # Use equal weights because the prompt does not expose numeric preference weights.
    weights: List[float] = [1.0 for _ in prefs]
    sw = float(len(weights)) or 1.0
    weights = [w / sw for w in weights]

    # utilities in [0,1], higher better
    u: Dict[OptionKey, List[float]] = {}
    for k in keys:
        o = options.get(k) or {}
        vals = []
        for p in prefs:
            field = p.get("field")
            direction = str(p.get("direction", "high"))
            norm = p.get("normalization") or {"type": "ordinal", "levels": [1, 2, 3, 4, 5]}
            vals.append(float(_normalize(_get_by_path(o, str(field)), norm, direction)))
        u[str(k)] = vals

    m = len(prefs)
    f_star = [max(u[k][j] for k in keys) for j in range(m)]
    f_minus = [min(u[k][j] for k in keys) for j in range(m)]

    def gap(j: int, val: float) -> float:
        denom = (f_star[j] - f_minus[j])
        if abs(denom) < 1e-12:
            return 0.0
        return (f_star[j] - val) / denom

    S: Dict[OptionKey, float] = {}
    R: Dict[OptionKey, float] = {}
    for k in keys:
        terms = [weights[j] * gap(j, u[k][j]) for j in range(m)]
        S[k] = float(sum(terms))
        R[k] = float(max(terms) if terms else 0.0)

    S_star, S_minus = min(S.values()), max(S.values())
    R_star, R_minus = min(R.values()), max(R.values())

    def norm01(x: float, lo: float, hi: float) -> float:
        if abs(hi - lo) < 1e-12:
            return 0.0
        return (x - lo) / (hi - lo)

    Q: Dict[OptionKey, float] = {}
    for k in keys:
        Q[k] = float(v * norm01(S[k], S_star, S_minus) + (1 - v) * norm01(R[k], R_star, R_minus))

    pick = min(Q.keys(), key=lambda kk: (Q[kk], ord(str(kk))))  # smaller better; tie-break A
    return str(pick), {"method": "vikor", "Q": Q, "S": S, "R": R, "feasible": keys, "weights": weights, "v": v}


def _pick_feasible_random(question: Mapping[str, Any], *, rng: random.Random) -> OptionKey:
    feasible = _feasible_keys(question)
    keys = feasible if feasible else ["A", "B", "C", "D"]
    return str(rng.choice(keys))


def _pick_simple_heuristic(question: Mapping[str, Any]) -> OptionKey:
    """
    Simple non-LLM heuristic.

    It does not use `oracle_scores` and does not reproduce the full preference
    weighting. The logic is: filter by `must`, then sort lexicographically by a
    small set of key fields.
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
                _int(o.get("handfeel_noise")),  # high is better per dataset definition
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
    Return a structure aligned with the LLM strategy output format:
      - pick: A/B/C/D
      - calls: []
      - raw_output: compact JSON with auditable details
    """
    if strategy not in NON_LLM_STRATEGIES:
        raise ValueError(f"Unknown non-LLM strategy: {strategy}")

    qid = str(question.get("id") or "")
    rng = random.Random(int(seed) if seed is not None else _stable_seed(qid))

    if strategy == "nonllm_feasible_random":
        pick = _pick_feasible_random(question, rng=rng)
        details: Dict[str, Any] = {"method": "feasible_random"}
    elif strategy == "nonllm_simple_heuristic":
        pick = _pick_simple_heuristic(question)
        details = {"method": "lexicographic_heuristic"}
    elif strategy == "nonllm_topsis":
        pick, details = _topsis_pick(question)
    elif strategy == "nonllm_vikor":
        pick, details = _vikor_pick(question, v=0.5)
    else:
        raise ValueError(f"Unknown non-LLM strategy: {strategy}")

    raw = json.dumps(
        {
            "strategy": strategy,
            "question_id": qid,
            "scenario": str(question.get("scenario") or ""),
            "pick": pick,
            "feasible": _feasible_keys(question),
            "details": details,
        },
        ensure_ascii=False,
    )
    return {"pick": pick, "calls": [], "raw_output": raw}

