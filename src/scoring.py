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
    Support nested-dict access with paths like `"a.b.c"`.
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
    Check hard `must` constraints.

    Returns:
      - ok: whether all constraints are satisfied
      - fail_list: reasons for failed constraints
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
    Normalize a single field to `[0, 1]`.

    Supported modes:
      - minmax: continuous numeric values
      - ordinal: ordered categorical / discrete levels
      - bool: boolean values
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
            # If no levels are provided, fall back to a common 1..5 scale.
            levels = [1, 2, 3, 4, 5]
        try:
            idx = levels.index(value)
        except ValueError:
            # Try to coerce numeric/string values onto the declared levels.
            v = _to_float(value)
            lv = [_to_float(x) for x in levels]
            if v is not None and all(x is not None for x in lv):
                # Pick the nearest declared level.
                idx = min(range(len(lv)), key=lambda i: abs(lv[i] - v))  # type: ignore[operator]
            else:
                return 0.0

        denom = max(1, len(levels) - 1)
        raw = idx / denom
        return raw if direction == "high" else 1.0 - raw

    raise ValueError(f"Unsupported normalization type: {ntype}")


def score_candidate(candidate: Mapping[str, Any], rules: Mapping[str, Any]) -> float:
    """
    Score a candidate by weighted `prefer` aggregation after `must` filtering.

    - if `must` fails: return `-inf`
    - for `prefer`: normalize each field to `[0,1]` and combine by weight
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
    Comparison value used for tie-breakers.

    - numeric: use float; missing becomes ±inf so it is always worst
    - string: use extreme sentinel values for missing so it is always worst
    """

    v = _get_by_path(candidate, field)
    if v is None:
        if direction == "high":
        # high: larger is better, so missing should be very small
            return float("-inf")
        return float("inf")

    if isinstance(v, bool):
        v = 1.0 if v else 0.0
    if isinstance(v, (int, float)):
        return float(v)

    # string / other
    if isinstance(v, str):
        # For string fields such as `id`, do not coerce to numeric values.
        return v

    # Fallback: coerce to numeric when possible.
    fv = _to_float(v)
    if fv is None:
        return str(v)
    return fv


def pick_best(
    candidates: Mapping[OptionKey, Mapping[str, Any]],
    rules: Mapping[str, Any],
) -> Tuple[OptionKey, Dict[OptionKey, float]]:
    """
    Select the best option from the A/B/C/D candidates.

    Returns:
      - best_key: "A"/"B"/"C"/"D"
      - scores: score for each candidate (`-inf` for must-fail)
    """

    scores: Dict[OptionKey, float] = {k: score_candidate(v, rules) for k, v in candidates.items()}

    # First select by score.
    best_score = max(scores.values()) if scores else float("-inf")
    tied: List[OptionKey] = [k for k, s in scores.items() if math.isclose(s, best_score) or s == best_score]
    if len(tied) == 1:
        return tied[0], scores

    # Tie-breakers.
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

    # Still tied: pick by stable option-key order for reproducibility.
    return sorted(tied)[0], scores


def describe_prefer(rules: Mapping[str, Any]) -> List[str]:
    """
    Optional helper that turns `prefer` entries into human-readable labels.
    """

    out: List[str] = []
    for p in rules.get("prefer", []):
        reason = p.get("reason") or p.get("field")
        w = p.get("weight", 0)
        out.append(f"{reason} (w={w})")
    return out


