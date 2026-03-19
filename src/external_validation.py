from __future__ import annotations

"""
Build external-validation question sets from small real catalogs.

Reads a scenario catalog CSV, optionally derives ordinal fields from `*_raw`
columns, filters rules by field coverage, and writes MCQ questions plus
metadata for the normal eval pipeline.
"""

import csv
import json
import random
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

import typer

from .scoring import pick_best, score_candidate


OptionKey = str  # "A"/"B"/"C"/"D"


def _read_csv(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [dict(r) for r in reader]


def _write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def _to_bool(x: Any) -> Optional[bool]:
    if x is None:
        return None
    if isinstance(x, bool):
        return bool(x)
    s = str(x).strip().lower()
    if s in ("", "none", "null", "na", "n/a"):
        return None
    if s in ("1", "true", "t", "yes", "y"):
        return True
    if s in ("0", "false", "f", "no", "n"):
        return False
    return None


def _to_int(x: Any) -> Optional[int]:
    if x is None:
        return None
    if isinstance(x, bool):
        return int(x)
    if isinstance(x, int):
        return int(x)
    s = str(x).strip()
    if s == "" or s.lower() in ("none", "null", "na", "n/a"):
        return None
    try:
        return int(float(s))
    except Exception:
        return None


def _to_float(x: Any) -> Optional[float]:
    if x is None:
        return None
    if isinstance(x, bool):
        return 1.0 if x else 0.0
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).strip()
    if s == "" or s.lower() in ("none", "null", "na", "n/a"):
        return None
    try:
        return float(s)
    except Exception:
        return None


def _set_by_path(obj: Dict[str, Any], path: str, value: Any) -> None:
    cur: Dict[str, Any] = obj
    parts = path.split(".")
    for p in parts[:-1]:
        if p not in cur or not isinstance(cur[p], dict):
            cur[p] = {}
        cur = cur[p]
    cur[parts[-1]] = value


def _get_by_path(obj: Mapping[str, Any], path: str) -> Any:
    cur: Any = obj
    for part in path.split("."):
        if not isinstance(cur, Mapping) or part not in cur:
            return None
        cur = cur[part]
    return cur


def _parse_row_to_candidate(row: Mapping[str, Any], *, scenario: str) -> Dict[str, Any]:
    """
    CSV -> candidate dict compatible with scoring/prompts.
    Supports nested keys like "compliance.pfas_free", "care.machine_wash".
    """
    out: Dict[str, Any] = {"scenario": scenario}

    # core id + optional provenance
    rid = str(row.get("id") or "").strip()
    if not rid:
        raise ValueError("CSV row missing required column: id")
    out["id"] = rid
    if row.get("source_url"):
        out["source_url"] = str(row.get("source_url")).strip()
    if row.get("source_name"):
        out["source_name"] = str(row.get("source_name")).strip()

    # numeric/ordinal fields (common subset)
    scalar_fields_float = ["weight_gsm", "loft_or_clo"]
    scalar_fields_int = [
        "water_repellency",
        "breathability",
        "abrasion",
        "handfeel_noise",
        "wind_blocking",
        "moisture_management",
        "bulk_weight",
        "cost_level",
        "lead_time_level",
    ]
    for k in scalar_fields_float:
        v = _to_float(row.get(k))
        if v is not None:
            out[k] = v
    for k in scalar_fields_int:
        v = _to_int(row.get(k))
        if v is not None:
            out[k] = v

    # nested booleans
    # prefer dot-path columns; also accept underscored aliases for convenience.
    pfas = _to_bool(row.get("compliance.pfas_free"))
    if pfas is None:
        pfas = _to_bool(row.get("compliance_pfas_free"))
    if pfas is not None:
        _set_by_path(out, "compliance.pfas_free", bool(pfas))

    mw = _to_bool(row.get("care.machine_wash"))
    if mw is None:
        mw = _to_bool(row.get("care_machine_wash"))
    if mw is not None:
        _set_by_path(out, "care.machine_wash", bool(mw))

    # keep any *_raw columns for optional derivation
    for k, v in row.items():
        if isinstance(k, str) and k.endswith("_raw"):
            fv = _to_float(v)
            if fv is not None:
                out[k] = fv

    return out


def _quantile_bins(values: List[float], q: int = 5) -> List[float]:
    """
    Return cut points for q quantile bins: (q-1) thresholds.
    Very small n: fall back to evenly spaced across min..max.
    """
    if not values:
        return []
    vs = sorted(values)
    if len(vs) < q:
        vmin, vmax = vs[0], vs[-1]
        if vmin == vmax:
            return [vmin] * (q - 1)
        step = (vmax - vmin) / q
        return [vmin + step * i for i in range(1, q)]
    cuts: List[float] = []
    for i in range(1, q):
        # nearest-rank
        idx = int(round((len(vs) - 1) * (i / q)))
        cuts.append(vs[idx])
    return cuts


def _bucket_1_to_5(x: float, cuts: List[float], *, direction: str = "high") -> int:
    # cuts length=4 for quintiles
    lvl = 1
    for c in cuts:
        if x >= c:
            lvl += 1
    lvl = max(1, min(5, lvl))
    if direction == "low":
        lvl = 6 - lvl
    return int(lvl)


def _derive_ordinals_from_raw(catalog: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    If the catalog contains *_raw numeric columns, derive 1..5 ordinals:
      - X_raw -> X  (direction configurable via mapping below)
    Returns a small report for logging/debug.
    """
    mapping = {
        "water_repellency_raw": ("water_repellency", "high"),
        "breathability_raw": ("breathability", "high"),
        "abrasion_raw": ("abrasion", "high"),
        "handfeel_noise_raw": ("handfeel_noise", "high"),
        "wind_blocking_raw": ("wind_blocking", "high"),
        "moisture_management_raw": ("moisture_management", "high"),
        "bulk_weight_raw": ("bulk_weight", "low"),
    }

    report: Dict[str, Dict[str, Any]] = {}
    for raw_key, (dst_key, direction) in mapping.items():
        xs = [float(c[raw_key]) for c in catalog if c.get(raw_key) is not None]
        if len(xs) < 8:
            continue
        cuts = _quantile_bins(xs, q=5)
        changed = 0
        for c in catalog:
            if c.get(dst_key) is not None:
                continue
            if c.get(raw_key) is None:
                continue
            c[dst_key] = _bucket_1_to_5(float(c[raw_key]), cuts, direction=direction)
            changed += 1
        report[dst_key] = {"from": raw_key, "direction": direction, "n_raw": len(xs), "imputed": changed, "cuts": cuts}
    return report


def _field_coverage(catalog: List[Dict[str, Any]], field: str) -> float:
    if not catalog:
        return 0.0
    present = 0
    for c in catalog:
        v = _get_by_path(c, field)
        if v is not None:
            present += 1
    return present / max(1, len(catalog))


def _filter_rules_by_coverage(rules: Dict[str, Any], catalog: List[Dict[str, Any]], min_coverage: float) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Drop must/prefer/tie_breakers for fields that are too sparse in the provided real catalog.
    This lets users map only a subset of fields.
    """
    dropped: Dict[str, Any] = {"must": [], "prefer": [], "tie_breakers": []}

    must_out = []
    for m in rules.get("must", []):
        f = str(m.get("field"))
        cov = _field_coverage(catalog, f)
        if cov >= min_coverage:
            must_out.append(m)
        else:
            dropped["must"].append({**m, "coverage": cov})

    prefer_out = []
    for p in rules.get("prefer", []):
        f = str(p.get("field"))
        cov = _field_coverage(catalog, f)
        if cov >= min_coverage:
            prefer_out.append(p)
        else:
            dropped["prefer"].append({**p, "coverage": cov})

    tb_out = []
    for tb in rules.get("tie_breakers", []):
        f = str(tb.get("field"))
        if f == "id":
            tb_out.append(tb)
            continue
        cov = _field_coverage(catalog, f)
        if cov >= min_coverage:
            tb_out.append(tb)
        else:
            dropped["tie_breakers"].append({**tb, "coverage": cov})

    # Renormalize prefer weights (so score is comparable even after dropping fields).
    total_w = sum(float(p.get("weight", 0.0)) for p in prefer_out)
    if total_w > 0:
        prefer_out = [{**p, "weight": float(p.get("weight", 0.0)) / total_w} for p in prefer_out]

    out_rules = {**rules, "must": must_out, "prefer": prefer_out, "tie_breakers": tb_out}
    return out_rules, dropped


def _scenario_stem(scenario: str, must_list: List[Dict[str, Any]], prefer_list: List[Dict[str, Any]]) -> str:
    def _must_text(ms: List[Dict[str, Any]]) -> str:
        parts = [m.get("reason") or f"{m.get('field')} {m.get('op')} {m.get('value')}" for m in ms]
        return "; ".join([p for p in parts if p]) if parts else "(none)"

    def _prefer_text(ps: List[Dict[str, Any]]) -> str:
        parts = [p.get("reason") or str(p.get("field")) for p in ps]
        return "; ".join([p for p in parts if p]) if parts else "(none)"

    if scenario == "outdoor_dwr_windbreaker":
        return (
            "Task: select the most suitable fabric for a lightweight outdoor DWR windbreaker.\n"
            f"Hard constraints (must): {_must_text(must_list)}.\n"
            f"Soft preferences (prefer, weighted): {_prefer_text(prefer_list)}.\n"
            "Choose the best option among the four candidates (A/B/C/D)."
        )
    if scenario == "winter_warm_midlayer":
        return (
            "Task: select the most suitable fabric/material option for a winter warm midlayer "
            "(synthetic insulation or fleece).\n"
            f"Hard constraints (must): {_must_text(must_list)}.\n"
            f"Soft preferences (prefer, weighted): {_prefer_text(prefer_list)}.\n"
            "Choose the best option among the four candidates (A/B/C/D)."
        )
    raise ValueError(f"Unknown scenario: {scenario}")


def _sample_must(rng: random.Random, must_pool: List[Dict[str, Any]], n_min: int, n_max: int) -> List[Dict[str, Any]]:
    if not must_pool:
        return []
    n = rng.randint(n_min, n_max)
    shuffled = must_pool[:]
    rng.shuffle(shuffled)
    # de-dup by field (avoid multiple thresholds on same field)
    used: set[str] = set()
    out: List[Dict[str, Any]] = []
    for m in shuffled:
        f = str(m.get("field"))
        if f in used:
            continue
        out.append(m)
        used.add(f)
        if len(out) >= n:
            break
    return out


def _generate_questions(
    *,
    rng: random.Random,
    scenario: str,
    catalog: List[Dict[str, Any]],
    base_rules: Dict[str, Any],
    n_questions: int,
    min_margin: float,
    max_attempts: int,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    if len(catalog) < 6:
        raise ValueError("Need at least 6 catalog items to generate non-trivial 4-way questions.")

    # Start from benchmark-style must templates when possible.
    if scenario == "outdoor_dwr_windbreaker":
        must_templates = [
            {"field": "water_repellency", "op": "gte", "value": 3, "reason": "Water repellency must be at least 3/5"},
            {"field": "water_repellency", "op": "gte", "value": 4, "reason": "Water repellency must be at least 4/5"},
            {"field": "breathability", "op": "gte", "value": 3, "reason": "Breathability must be at least 3/5"},
            {"field": "abrasion", "op": "gte", "value": 3, "reason": "Abrasion resistance must be at least 3/5 (outdoor use)"},
            {"field": "abrasion", "op": "gte", "value": 4, "reason": "Abrasion resistance must be at least 4/5 (high-intensity outdoor use)"},
            {"field": "weight_gsm", "op": "lte", "value": 150, "reason": "Weight must not exceed 150 gsm"},
            {"field": "weight_gsm", "op": "lte", "value": 120, "reason": "Weight must not exceed 120 gsm (lightweight requirement)"},
            {"field": "cost_level", "op": "lte", "value": 3, "reason": "Cost level must not exceed 3 (budget constraint)"},
            {"field": "lead_time_level", "op": "lte", "value": 3, "reason": "Lead-time level must not exceed 3 (fast launch)"},
            {"field": "compliance.pfas_free", "op": "eq", "value": True, "reason": "PFAS-free is required (compliance/sustainability)"},
        ]
    else:
        must_templates = [
            {"field": "care.machine_wash", "op": "eq", "value": True, "reason": "Machine washable is required (care constraint)"},
            {"field": "loft_or_clo", "op": "gte", "value": 1.2, "reason": "Thermal insulation (loft/clo) must be at least 1.2"},
            {"field": "loft_or_clo", "op": "gte", "value": 1.5, "reason": "Thermal insulation (loft/clo) must be at least 1.5 (high warmth)"},
            {"field": "moisture_management", "op": "gte", "value": 3, "reason": "Moisture management must be at least 3/5"},
            {"field": "moisture_management", "op": "gte", "value": 4, "reason": "Moisture management must be at least 4/5 (high-activity use)"},
            {"field": "wind_blocking", "op": "gte", "value": 3, "reason": "Wind blocking must be at least 3/5"},
            {"field": "bulk_weight", "op": "lte", "value": 3, "reason": "Bulk must not exceed level 3 (low-bulk requirement)"},
            {"field": "cost_level", "op": "lte", "value": 4, "reason": "Cost level must not exceed 4"},
            {"field": "lead_time_level", "op": "lte", "value": 3, "reason": "Lead-time level must not exceed 3"},
            {"field": "compliance.pfas_free", "op": "eq", "value": True, "reason": "PFAS-free is required (compliance/sustainability)"},
        ]

    # Keep only templates for fields that exist in this catalog.
    cov = {m["field"]: _field_coverage(catalog, m["field"]) for m in must_templates}
    must_pool = [m for m in must_templates if cov.get(m["field"], 0.0) > 0.0]
    if not must_pool:
        must_pool = list(base_rules.get("must") or [])

    out: List[Dict[str, Any]] = []
    attempts = 0
    margins: List[float] = []
    must_counts: Counter = Counter()

    while len(out) < n_questions and attempts < max_attempts:
        attempts += 1

        # sample 4 options
        opts = rng.sample(catalog, 4)
        keys = ["A", "B", "C", "D"]
        rng.shuffle(keys)
        options: Dict[OptionKey, Dict[str, Any]] = {keys[i]: opts[i] for i in range(4)}

        # sample must subset + fixed prefer/tie-breakers from base_rules
        must_list = _sample_must(rng, must_pool, n_min=2, n_max=min(4, max(2, len(must_pool))))
        rules = {
            "must": must_list,
            "prefer": list(base_rules.get("prefer") or []),
            "tie_breakers": list(base_rules.get("tie_breakers") or []),
        }

        best_key, scores = pick_best(options, rules)
        # require at least 2 feasible options (otherwise margin is meaningless)
        finite_scores = [float(s) for s in scores.values() if float(s) != float("-inf")]
        if len(finite_scores) < 2:
            continue
        finite_scores_sorted = sorted(finite_scores, reverse=True)
        margin = float(finite_scores_sorted[0] - finite_scores_sorted[1])
        if margin < float(min_margin):
            continue

        # also avoid degenerate case where all are must-fail (should be covered by finite_scores)
        answer = best_key
        stem = _scenario_stem(scenario, must_list, rules["prefer"])

        qid = f"ext_{scenario}_{len(out)+1:05d}"
        out.append(
            {
                "id": qid,
                "scenario": scenario,
                "stem": stem,
                "options": options,
                "answer": answer,
                "key_rationales": [],
                "option_tags": None,  # external set doesn't have generator-style tags
                "meta": {
                    "source": "external_validation",
                    "oracle_scores": {k: (None if float(v) == float("-inf") else round(float(v), 6)) for k, v in scores.items()},
                    "margin": round(float(margin), 6),
                    "must_sample": [m.get("reason") for m in must_list],
                },
            }
        )
        margins.append(margin)
        for m in must_list:
            must_counts[str(m.get("reason") or m.get("field"))] += 1

    report = {
        "scenario": scenario,
        "n_catalog": len(catalog),
        "n_questions": len(out),
        "attempts": attempts,
        "accept_rate": (len(out) / max(1, attempts)),
        "min_margin": float(min_margin),
        "margin_median": (sorted(margins)[len(margins) // 2] if margins else None),
        "must_usage": dict(must_counts.most_common()),
    }
    return out, report


app = typer.Typer(add_completion=False, help="Build external validation question sets from real datasheet catalogs.")


@dataclass
class BuildResult:
    questions: List[Dict[str, Any]]
    report: Dict[str, Any]
    rules_used: Dict[str, Any]
    dropped: Dict[str, Any]
    derived: Dict[str, Any]


def _build(
    *,
    scenario: str,
    catalog_csv: Path,
    rules_path: Path,
    n_questions: int,
    seed: int,
    min_margin: float,
    min_coverage: float,
    derive_ordinals: bool,
) -> BuildResult:
    rows = _read_csv(catalog_csv)
    catalog: List[Dict[str, Any]] = [_parse_row_to_candidate(r, scenario=scenario) for r in rows]

    derived_report: Dict[str, Any] = {}
    if derive_ordinals:
        derived_report = _derive_ordinals_from_raw(catalog)

    rules = json.loads(rules_path.read_text(encoding="utf-8"))
    rules_used, dropped = _filter_rules_by_coverage(rules, catalog, min_coverage=min_coverage)

    rng = random.Random(seed)
    questions, gen_report = _generate_questions(
        rng=rng,
        scenario=scenario,
        catalog=catalog,
        base_rules=rules_used,
        n_questions=n_questions,
        min_margin=min_margin,
        max_attempts=max(5000, n_questions * 200),
    )
    return BuildResult(
        questions=questions,
        report={
            **gen_report,
            "catalog_csv": str(catalog_csv),
            "rules_path": str(rules_path),
            "min_coverage": float(min_coverage),
            "derive_ordinals": bool(derive_ordinals),
        },
        rules_used=rules_used,
        dropped=dropped,
        derived=derived_report,
    )


@app.command()
def inspect(
    scenario: str = typer.Option(..., help="outdoor_dwr_windbreaker / winter_warm_midlayer"),
    catalog_csv: Path = typer.Option(..., help="CSV catalog for the scenario"),
    rules_path: Path = typer.Option(..., help="rules_*.json (same oracle as main experiments)"),
    min_coverage: float = typer.Option(0.7, help="Keep a field in rules only if coverage >= this threshold"),
    derive_ordinals: bool = typer.Option(True, "--derive-ordinals/--no-derive-ordinals", help="Derive 1..5 fields from *_raw columns when possible"),
) -> None:
    res = _build(
        scenario=scenario,
        catalog_csv=catalog_csv,
        rules_path=rules_path,
        n_questions=20,
        seed=1,
        min_margin=0.01,
        min_coverage=min_coverage,
        derive_ordinals=derive_ordinals,
    )
    typer.echo(json.dumps({"derived": res.derived, "dropped": res.dropped, "rules_used": res.rules_used}, ensure_ascii=False, indent=2))


@app.command()
def build(
    scenario: str = typer.Option(..., help="outdoor_dwr_windbreaker / winter_warm_midlayer"),
    catalog_csv: Path = typer.Option(..., help="CSV catalog for the scenario"),
    rules_path: Path = typer.Option(..., help="rules_*.json (same oracle as main experiments)"),
    out_questions: Path = typer.Option(..., help="Output questions jsonl (to be used by src.eval_run)"),
    out_meta: Optional[Path] = typer.Option(None, help="Optional: write a meta/report JSON next to questions"),
    n_questions: int = typer.Option(200, help="How many external questions to generate"),
    seed: int = typer.Option(42, help="Random seed"),
    min_margin: float = typer.Option(0.05, help="Minimum oracle margin (top1-top2) to keep a question"),
    min_coverage: float = typer.Option(0.7, help="Keep a field in rules only if coverage >= this threshold"),
    derive_ordinals: bool = typer.Option(True, "--derive-ordinals/--no-derive-ordinals", help="Derive 1..5 fields from *_raw columns when possible"),
) -> None:
    res = _build(
        scenario=scenario,
        catalog_csv=catalog_csv,
        rules_path=rules_path,
        n_questions=n_questions,
        seed=seed,
        min_margin=min_margin,
        min_coverage=min_coverage,
        derive_ordinals=derive_ordinals,
    )

    _write_jsonl(out_questions, res.questions)
    typer.echo(f"Wrote questions -> {out_questions} (n={len(res.questions)})")

    meta_obj = {"report": res.report, "derived": res.derived, "dropped": res.dropped, "rules_used": res.rules_used}
    if out_meta is None:
        out_meta = out_questions.with_suffix(".meta.json")
    out_meta.parent.mkdir(parents=True, exist_ok=True)
    out_meta.write_text(json.dumps(meta_obj, ensure_ascii=False, indent=2), encoding="utf-8")
    typer.echo(f"Wrote meta -> {out_meta}")


if __name__ == "__main__":
    app()

