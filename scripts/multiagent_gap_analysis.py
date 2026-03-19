from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

import pandas as pd

# Ensure repo root is on sys.path so `import src.*` works when running as a script.
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.scoring import check_must  # noqa: E402
from src.strategies_multi import WEIGHTS_OUTDOOR, WEIGHTS_WINTER, _parse_agent_decision  # noqa: E402


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _reason_to_must_cond_map() -> Dict[str, Dict[str, Any]]:
    """
    Mirror logic in src/strategies_non_llm.py to map meta.must_sample reasons
    back to concrete must-condition dicts (from dataset_v1 templates).
    """
    from src import dataset_v1 as dv1  # local import

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


def _is_option_must_fail(question: Mapping[str, Any], pick: Optional[str]) -> Optional[bool]:
    if pick not in ("A", "B", "C", "D"):
        return None
    tags = (question.get("option_tags") or {}).get(pick) or []
    return "must_fail" in set(tags)


def _must_violation_fields(question: Mapping[str, Any], pick: Optional[str]) -> List[str]:
    if pick not in ("A", "B", "C", "D"):
        return []
    rules = _build_rules_from_question(question)
    opt = (question.get("options") or {}).get(pick) or {}
    ok, reasons = check_must(opt, rules)
    if ok:
        return []
    # parse "field op value" style reasons if present; fallback to full text
    out: List[str] = []
    for r in reasons:
        s = str(r)
        if "field=" in s:
            out.append(s)
        else:
            out.append(s)
    return out


def _is_feasible(question: Mapping[str, Any], pick: Optional[str]) -> bool:
    if pick not in ("A", "B", "C", "D"):
        return False
    rules = _build_rules_from_question(question)
    opt = (question.get("options") or {}).get(pick) or {}
    ok, _ = check_must(opt, rules)
    return bool(ok)


def _feasibility_corrected_pick(
    *,
    scenario: str,
    agent_decisions: Mapping[str, Dict[str, Any]],
    question: Mapping[str, Any],
    mode: str,
) -> Optional[str]:
    """
    Counterfactual ablation (no new LLM calls):
    re-aggregate agent picks after filtering out picks that violate must constraints
    using a deterministic checker (instead of relying on self-reported must_fail).
    """
    picks: List[Tuple[str, Optional[str], float]] = []
    for role, d in agent_decisions.items():
        p = d.get("pick")
        p = str(p) if p in ("A", "B", "C", "D") else None
        conf = float(d.get("confidence", 0.5))
        picks.append((role, p, conf))

    filt = [(role, p, conf) for (role, p, conf) in picks if _is_feasible(question, p)]
    if not filt:
        return None

    if mode == "voting":
        cnt: Dict[str, float] = {k: 0.0 for k in ("A", "B", "C", "D")}
        conf_sum: Dict[str, float] = {k: 0.0 for k in ("A", "B", "C", "D")}
        for _, p, conf in filt:
            if p in cnt:
                cnt[p] += 1.0
                conf_sum[p] += conf
        return max(cnt.keys(), key=lambda k: (cnt[k], conf_sum[k], -ord(k)))

    # weighted (role-weight * confidence)
    rw = WEIGHTS_OUTDOOR if scenario == "outdoor_dwr_windbreaker" else WEIGHTS_WINTER
    scores: Dict[str, float] = {k: 0.0 for k in ("A", "B", "C", "D")}
    for role, p, conf in filt:
        if p not in scores:
            continue
        w = float(rw.get(str(role), 1.0))
        scores[p] += w * conf
    return max(scores.keys(), key=lambda k: (scores[k], -ord(k)))


@dataclass(frozen=True)
class AgentRow:
    question_id: str
    strategy: str
    scenario: str
    role: str
    agent_pick: Optional[str]
    agent_must_fail_flag: bool
    agent_llm_error: bool
    agent_pick_is_must_fail: Optional[bool]


def main() -> None:
    root = _ROOT
    log_path = root / "outputs" / "per_question_log_main.jsonl"
    q_path = root / "data" / "questions_v1_clean.jsonl"
    out_dir = root / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)

    log_rows = _load_jsonl(log_path)
    questions = _load_jsonl(q_path)
    q_by_id = {str(q["id"]): q for q in questions}

    # 1) Per-strategy top-level metrics + must violation on valid preds.
    rows_main: List[Dict[str, Any]] = []

    # 2) Agent-level calibration rows (for multi-agent only)
    agent_rows: List[AgentRow] = []

    # 3) Violation field attribution
    vio_field_counts: Dict[Tuple[str, str], Counter[str]] = defaultdict(Counter)  # (strategy, scenario)->Counter

    # 4) Counterfactual: feasibility-corrected aggregation (no new calls)
    corrected_rows: List[Dict[str, Any]] = []

    for r in log_rows:
        strategy = str(r.get("strategy") or "")
        scenario = str(r.get("scenario") or "")
        qid = str(r.get("question_id") or "")
        pred = r.get("pred")
        pred = str(pred) if pred is not None else None

        q = q_by_id.get(qid)
        if q is None:
            continue

        valid = pred in ("A", "B", "C", "D")
        pred_is_must_fail = _is_option_must_fail(q, pred) if valid else None
        if valid and pred_is_must_fail:
            for fld in _must_violation_fields(q, pred):
                vio_field_counts[(strategy, scenario)][fld] += 1

        rows_main.append(
            {
                "strategy": strategy,
                "scenario": scenario,
                "question_id": qid,
                "valid": bool(valid),
                "is_correct": bool(r.get("is_correct")),
                "pred_is_must_fail": bool(pred_is_must_fail) if pred_is_must_fail is not None else None,
            }
        )

        # Agent-level extraction: only for strategies that have role calls
        calls = r.get("calls") or []
        if not isinstance(calls, list) or not calls:
            continue

        # Heuristic: multi-agent calls contain "role" field
        has_role = any(isinstance(c, Mapping) and "role" in c for c in calls)
        if not has_role:
            continue

        # Collect per-role decisions for this question
        by_role: Dict[str, Dict[str, Any]] = {}
        for c in calls:
            if not isinstance(c, Mapping):
                continue
            role = str(c.get("role") or "")
            resp = str(c.get("response_text") or "")
            d = _parse_agent_decision(resp)
            apick = d.get("pick")
            apick = str(apick) if apick in ("A", "B", "C", "D") else None
            if role:
                by_role[role] = d
            agent_rows.append(
                AgentRow(
                    question_id=qid,
                    strategy=strategy,
                    scenario=scenario,
                    role=role,
                    agent_pick=apick,
                    agent_must_fail_flag=bool(d.get("must_fail")),
                    agent_llm_error=bool(d.get("llm_error")),
                    agent_pick_is_must_fail=_is_option_must_fail(q, apick),
                )
            )

        # Compute corrected pick for voting/weighted-like strategies
        if by_role:
            mode = "weighted" if strategy in ("weighted_voting", "garmentagents_fixed", "garmentagents_adaptive") else "voting"
            corr = _feasibility_corrected_pick(scenario=scenario, agent_decisions=by_role, question=q, mode=mode)
            corrected_rows.append(
                {
                    "strategy": strategy,
                    "scenario": scenario,
                    "question_id": qid,
                    "corrected_pred": corr,
                    "corrected_valid": corr in ("A", "B", "C", "D"),
                    "corrected_is_correct": bool(corr == str(r.get("gold"))),
                }
            )

    df = pd.DataFrame(rows_main)
    df_summary = (
        df.groupby(["strategy", "scenario"], dropna=False)
        .agg(
            n=("question_id", "count"),
            acc=("is_correct", "mean"),
            valid_rate=("valid", "mean"),
            must_violation_on_valid=("pred_is_must_fail", lambda s: float(pd.Series([x for x in s if x is not None]).mean()) if any(x is not None for x in s) else float("nan")),
        )
        .reset_index()
    )

    # Overall (across scenarios) summary
    df_overall = (
        df.groupby(["strategy"], dropna=False)
        .agg(
            n=("question_id", "count"),
            acc=("is_correct", "mean"),
            valid_rate=("valid", "mean"),
            must_violation_on_valid=("pred_is_must_fail", lambda s: float(pd.Series([x for x in s if x is not None]).mean()) if any(x is not None for x in s) else float("nan")),
        )
        .reset_index()
        .sort_values(["acc", "valid_rate"], ascending=False)
    )

    out_main_csv = out_dir / "multiagent_gap_summary.csv"
    out_overall_csv = out_dir / "multiagent_gap_summary_overall.csv"
    df_summary.to_csv(out_main_csv, index=False)
    df_overall.to_csv(out_overall_csv, index=False)

    # Agent calibration
    if agent_rows:
        ar = pd.DataFrame([a.__dict__ for a in agent_rows])
        # Consider only cases where agent produced a valid pick
        ar_valid = ar[ar["agent_pick"].isin(["A", "B", "C", "D"])].copy()

        # Confusion matrix: must_fail flag vs actual must-fail of picked option
        # - FN: actual must-fail but flag False
        # - FP: actual feasible but flag True
        def _rates(g: pd.DataFrame) -> pd.Series:
            known = g[g["agent_pick_is_must_fail"].notna()]
            if known.empty:
                return pd.Series({"n": 0})
            actual = known["agent_pick_is_must_fail"].astype(bool)
            flag = known["agent_must_fail_flag"].astype(bool)
            fn = int(((actual == True) & (flag == False)).sum())
            fp = int(((actual == False) & (flag == True)).sum())
            tp = int(((actual == True) & (flag == True)).sum())
            tn = int(((actual == False) & (flag == False)).sum())
            n = int(len(known))
            return pd.Series(
                {
                    "n": n,
                    "tp": tp,
                    "tn": tn,
                    "fp": fp,
                    "fn": fn,
                    "fn_rate_on_actual_mustfail": (fn / (tp + fn)) if (tp + fn) > 0 else float("nan"),
                    "fp_rate_on_actual_feasible": (fp / (fp + tn)) if (fp + tn) > 0 else float("nan"),
                }
            )

        calib = ar_valid.groupby(["strategy", "scenario", "role"]).apply(_rates).reset_index()
        calib_overall = ar_valid.groupby(["strategy"]).apply(_rates).reset_index()

        calib.to_csv(out_dir / "multiagent_mustfail_calibration_by_role.csv", index=False)
        calib_overall.to_csv(out_dir / "multiagent_mustfail_calibration_overall.csv", index=False)

    # Violation field attribution (top fields)
    field_rows: List[Dict[str, Any]] = []
    for (strategy, scenario), ctr in vio_field_counts.items():
        total = sum(ctr.values()) or 1
        for fld, c in ctr.most_common(20):
            field_rows.append(
                {
                    "strategy": strategy,
                    "scenario": scenario,
                    "field_or_reason": fld,
                    "count": int(c),
                    "share_within_strategy_scenario": float(c) / float(total),
                    "total_violations_strategy_scenario": int(total),
                }
            )
    pd.DataFrame(field_rows).to_csv(out_dir / "multiagent_must_violation_fields_top20.csv", index=False)

    # Counterfactual corrected summary
    if corrected_rows:
        cdf = pd.DataFrame(corrected_rows)
        csum = (
            cdf.groupby(["strategy"], dropna=False)
            .agg(
                n=("question_id", "count"),
                corrected_acc=("corrected_is_correct", "mean"),
                corrected_valid_rate=("corrected_valid", "mean"),
            )
            .reset_index()
        )
        csum.to_csv(out_dir / "multiagent_feasibility_corrected_summary_overall.csv", index=False)
        print(f"Wrote: {out_dir / 'multiagent_feasibility_corrected_summary_overall.csv'}")

    print(f"Wrote: {out_main_csv}")
    print(f"Wrote: {out_overall_csv}")
    if agent_rows:
        print(f"Wrote: {out_dir / 'multiagent_mustfail_calibration_by_role.csv'}")
        print(f"Wrote: {out_dir / 'multiagent_mustfail_calibration_overall.csv'}")
    print(f"Wrote: {out_dir / 'multiagent_must_violation_fields_top20.csv'}")


if __name__ == "__main__":
    main()

