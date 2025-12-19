from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Tuple

OptionKey = str  # typically "A"/"B"/"C"/"D"


def load_rules(path: str | Path) -> Dict[str, Any]:
    path = Path(path)
    return json.loads(path.read_text(encoding="utf-8"))


def _get_by_path(obj: Mapping[str, Any], path: str) -> Any:
    """
    支持用 "a.b.c" 访问嵌套 dict。
    """

    cur: Any = obj
    for part in path.split("."):
        if not isinstance(cur, Mapping):
            return None
        if part not in cur:
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
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def check_must(candidate: Mapping[str, Any], rules: Mapping[str, Any]) -> Tuple[bool, List[str]]:
    """
    检查硬约束 must。

    Returns:
      - ok: 是否全部满足
      - fail_list: 不满足的原因列表（可用于解释/生成干扰项标签）
    """

    fails: List[str] = []
    for cond in rules.get("must", []):
        field = cond["field"]
        op = cond.get("op", "eq")
        expected = cond.get("value")
        reason = cond.get("reason") or f"{field} {op} {expected}"

        actual = _get_by_path(candidate, field)

        ok = True
        if op == "eq":
            ok = actual == expected
        elif op == "ne":
            ok = actual != expected
        elif op in ("gt", "gte", "lt", "lte"):
            a = _to_float(actual)
            b = _to_float(expected)
            if a is None or b is None:
                ok = False
            elif op == "gt":
                ok = a > b
            elif op == "gte":
                ok = a >= b
            elif op == "lt":
                ok = a < b
            elif op == "lte":
                ok = a <= b
        elif op == "in":
            ok = actual in expected
        elif op == "not_in":
            ok = actual not in expected
        else:
            raise ValueError(f"Unsupported must op: {op}")

        if not ok:
            fails.append(reason)

    return (len(fails) == 0), fails


def _normalize(value: Any, normalization: Mapping[str, Any], direction: str) -> float:
    """
    将单个字段归一化到 [0,1]，支持：
      - minmax: 连续数值
      - ordinal: 有序等级/离散值
      - bool: 布尔
    """

    if value is None:
        return 0.0

    ntype = normalization.get("type", "ordinal")
    if ntype == "bool":
        v = 1.0 if bool(value) else 0.0
        return v if direction == "high" else 1.0 - v

    if ntype == "minmax":
        v = _to_float(value)
        vmin = _to_float(normalization.get("min"))
        vmax = _to_float(normalization.get("max"))
        if v is None or vmin is None or vmax is None:
            return 0.0
        if math.isclose(vmin, vmax):
            return 0.5
        raw = (v - vmin) / (vmax - vmin)
        raw = max(0.0, min(1.0, raw))
        return raw if direction == "high" else 1.0 - raw

    if ntype == "ordinal":
        levels: List[Any] = list(normalization.get("levels", []))
        if not levels:
            # 没提供 levels 就退化成 minmax（用常见 1..5）
            levels = [1, 2, 3, 4, 5]
        try:
            idx = levels.index(value)
        except ValueError:
            # 尝试把数字/字符串归一到 levels
            v = _to_float(value)
            lv = [_to_float(x) for x in levels]
            if v is not None and all(x is not None for x in lv):
                # 找最接近的
                idx = min(range(len(lv)), key=lambda i: abs(lv[i] - v))  # type: ignore[operator]
            else:
                return 0.0

        denom = max(1, len(levels) - 1)
        raw = idx / denom
        return raw if direction == "high" else 1.0 - raw

    raise ValueError(f"Unsupported normalization type: {ntype}")


def score_candidate(candidate: Mapping[str, Any], rules: Mapping[str, Any]) -> float:
    """
    对候选面料按 prefer 加权求和（并用 must 做淘汰）。

    - must 不满足：返回 -inf
    - prefer：字段归一化到 [0,1] 后按权重加权
    """

    ok, _fails = check_must(candidate, rules)
    if not ok:
        return float("-inf")

    prefs = rules.get("prefer", [])
    if not prefs:
        return 0.0

    total_w = sum(float(p.get("weight", 0.0)) for p in prefs)
    if total_w <= 0:
        total_w = 1.0

    score = 0.0
    for p in prefs:
        field = p["field"]
        w = float(p.get("weight", 0.0))
        direction = p.get("direction", "high")
        normalization = p.get("normalization", {"type": "ordinal", "levels": [1, 2, 3, 4, 5]})

        v = _get_by_path(candidate, field)
        nv = _normalize(v, normalization, direction)
        score += (w / total_w) * nv

    return float(score)


def _tie_value(candidate: Mapping[str, Any], field: str, direction: str) -> Any:
    """
    tie-breaker 的比较值：
    - 数值：用 float，missing 用 ±inf（missing 永远最差）
    - 字符串：missing 用极大/极小哨兵（missing 永远最差）
    """

    v = _get_by_path(candidate, field)
    if v is None:
        if direction == "high":
            # high: bigger is better, missing is worst => very small
            return float("-inf")
        return float("inf")

    if isinstance(v, bool):
        v = 1.0 if v else 0.0
    if isinstance(v, (int, float)):
        return float(v)

    # string / other
    if isinstance(v, str):
        # 对字符串 field（如 id）我们不做数值化；missing 已在上面处理。
        return v

    # fallback：尽量数值化
    fv = _to_float(v)
    if fv is None:
        return str(v)
    return fv


def pick_best(
    candidates: Mapping[OptionKey, Mapping[str, Any]],
    rules: Mapping[str, Any],
) -> Tuple[OptionKey, Dict[OptionKey, float]]:
    """
    从 A/B/C/D 候选里选择最优项。

    Returns:
      - best_key: "A"/"B"/"C"/"D"
      - scores: 每个候选的分数（must-fail 为 -inf）
    """

    scores: Dict[OptionKey, float] = {k: score_candidate(v, rules) for k, v in candidates.items()}

    # 先按分数取最大
    best_score = max(scores.values()) if scores else float("-inf")
    tied: List[OptionKey] = [k for k, s in scores.items() if math.isclose(s, best_score) or s == best_score]
    if len(tied) == 1:
        return tied[0], scores

    # tie-breakers
    for tb in rules.get("tie_breakers", []):
        field = tb["field"]
        direction = tb.get("direction", "high")

        if direction == "high":
            best_val = None
            new_tied: List[OptionKey] = []
            for k in tied:
                val = _tie_value(candidates[k], field, direction)
                if best_val is None or val > best_val:
                    best_val = val
                    new_tied = [k]
                elif val == best_val:
                    new_tied.append(k)
        else:
            best_val = None
            new_tied = []
            for k in tied:
                val = _tie_value(candidates[k], field, direction)
                if best_val is None or val < best_val:
                    best_val = val
                    new_tied = [k]
                elif val == best_val:
                    new_tied.append(k)

        tied = new_tied
        if len(tied) == 1:
            return tied[0], scores

    # 仍然平局：按 option key 稳定选择（保证可复现）
    return sorted(tied)[0], scores


def describe_prefer(rules: Mapping[str, Any]) -> List[str]:
    """
    可选：把 prefer 条目转成人类可读描述（用于 question/stem）。
    """

    out: List[str] = []
    for p in rules.get("prefer", []):
        reason = p.get("reason") or p.get("field")
        w = p.get("weight", 0)
        out.append(f"{reason}（w={w}）")
    return out


