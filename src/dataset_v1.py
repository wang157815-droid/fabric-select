"""
dataset_v1: assemble the v1 release of the semi-synthetic benchmark dataset,
run QC cleaning, and export metadata/report files.

This script is deterministic and rule-based. Question text, sampled
constraints, oracle labels, and QC filtering are assembled programmatically
from seeded randomness, fixed scenario templates, and a rule-based
scoring/oracle pipeline.

Usage:
    python -m src.dataset_v1 --seed 42 --n-outdoor 600 --n-winter 600 --clean-per-scenario 500

Outputs:
    data/questions_v1.jsonl          raw programmatically assembled question pool (>=1000)
    data/questions_v1_meta.json      must/prefer/difficulty statistics
    data/questions_v1_clean.jsonl    cleaned release set (exactly 500 per scenario)
    outputs/dataset_report.md        unique-answer rate, drop rate, distractor mix
"""

from __future__ import annotations

import json
import random
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Mapping, Tuple

import typer

from .scoring import check_must, load_rules, pick_best, score_candidate


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


# ─────────────────────────────────────────────────────────────────────────────
# Must-constraint templates. Each question samples 2-4 items for diversity.
# ─────────────────────────────────────────────────────────────────────────────

MUST_TEMPLATES_OUTDOOR: List[Dict[str, Any]] = [
    {"field": "compliance.pfas_free", "op": "eq", "value": True, "reason": "PFAS-free is required (compliance/sustainability)"},
    {"field": "water_repellency", "op": "gte", "value": 4, "reason": "Water repellency must be at least 4/5"},
    {"field": "water_repellency", "op": "gte", "value": 3, "reason": "Water repellency must be at least 3/5"},
    {"field": "abrasion", "op": "gte", "value": 3, "reason": "Abrasion resistance must be at least 3/5 (outdoor use)"},
    {"field": "abrasion", "op": "gte", "value": 4, "reason": "Abrasion resistance must be at least 4/5 (high-intensity outdoor use)"},
    {"field": "breathability", "op": "gte", "value": 3, "reason": "Breathability must be at least 3/5"},
    {"field": "weight_gsm", "op": "lte", "value": 120, "reason": "Weight must not exceed 120 gsm (lightweight requirement)"},
    {"field": "weight_gsm", "op": "lte", "value": 150, "reason": "Weight must not exceed 150 gsm"},
    {"field": "lead_time_level", "op": "lte", "value": 3, "reason": "Lead-time level must not exceed 3 (fast launch)"},
    {"field": "cost_level", "op": "lte", "value": 3, "reason": "Cost level must not exceed 3 (budget constraint)"},
]

MUST_TEMPLATES_WINTER: List[Dict[str, Any]] = [
    {"field": "care.machine_wash", "op": "eq", "value": True, "reason": "Machine washable is required (care constraint)"},
    {"field": "loft_or_clo", "op": "gte", "value": 1.2, "reason": "Thermal insulation (loft/clo) must be at least 1.2"},
    {"field": "loft_or_clo", "op": "gte", "value": 1.5, "reason": "Thermal insulation (loft/clo) must be at least 1.5 (high warmth)"},
    {"field": "moisture_management", "op": "gte", "value": 3, "reason": "Moisture management must be at least 3/5"},
    {"field": "moisture_management", "op": "gte", "value": 4, "reason": "Moisture management must be at least 4/5 (high-activity use)"},
    {"field": "wind_blocking", "op": "gte", "value": 3, "reason": "Wind blocking must be at least 3/5"},
    {"field": "bulk_weight", "op": "lte", "value": 3, "reason": "Bulk must not exceed level 3 (low-bulk requirement)"},
    {"field": "compliance.pfas_free", "op": "eq", "value": True, "reason": "PFAS-free is required (compliance/sustainability)"},
    {"field": "lead_time_level", "op": "lte", "value": 3, "reason": "Lead-time level must not exceed 3"},
    {"field": "cost_level", "op": "lte", "value": 4, "reason": "Cost level must not exceed 4"},
]

# Keep `prefer` aligned with `rules_*.json` for stable scoring.
PREFER_OUTDOOR: List[Dict[str, Any]] = [
    {"field": "water_repellency", "weight": 0.20, "direction": "high", "normalization": {"type": "ordinal", "levels": [1,2,3,4,5]}, "reason": "Stronger water repellency"},
    {"field": "breathability", "weight": 0.18, "direction": "high", "normalization": {"type": "ordinal", "levels": [1,2,3,4,5]}, "reason": "Higher breathability and comfort"},
    {"field": "abrasion", "weight": 0.15, "direction": "high", "normalization": {"type": "ordinal", "levels": [1,2,3,4,5]}, "reason": "Better abrasion resistance and durability"},
    {"field": "handfeel_noise", "weight": 0.10, "direction": "high", "normalization": {"type": "ordinal", "levels": [1,2,3,4,5]}, "reason": "Quieter with better handfeel"},
    {"field": "weight_gsm", "weight": 0.10, "direction": "low", "normalization": {"type": "minmax", "min": 60, "max": 180}, "reason": "Lower weight"},
    {"field": "cost_level", "weight": 0.15, "direction": "low", "normalization": {"type": "ordinal", "levels": [1,2,3,4,5]}, "reason": "Lower cost"},
    {"field": "lead_time_level", "weight": 0.12, "direction": "low", "normalization": {"type": "ordinal", "levels": [1,2,3,4,5]}, "reason": "Shorter lead time"},
]

PREFER_WINTER: List[Dict[str, Any]] = [
    {"field": "loft_or_clo", "weight": 0.30, "direction": "high", "normalization": {"type": "minmax", "min": 0.8, "max": 2.6}, "reason": "Higher warmth"},
    {"field": "wind_blocking", "weight": 0.15, "direction": "high", "normalization": {"type": "ordinal", "levels": [1,2,3,4,5]}, "reason": "Stronger wind blocking"},
    {"field": "moisture_management", "weight": 0.20, "direction": "high", "normalization": {"type": "ordinal", "levels": [1,2,3,4,5]}, "reason": "Better moisture management and quick-dry"},
    {"field": "bulk_weight", "weight": 0.15, "direction": "low", "normalization": {"type": "ordinal", "levels": [1,2,3,4,5]}, "reason": "Lower bulk"},
    {"field": "cost_level", "weight": 0.12, "direction": "low", "normalization": {"type": "ordinal", "levels": [1,2,3,4,5]}, "reason": "Lower cost"},
    {"field": "lead_time_level", "weight": 0.08, "direction": "low", "normalization": {"type": "ordinal", "levels": [1,2,3,4,5]}, "reason": "Shorter lead time"},
]

TIE_BREAKERS_OUTDOOR = [
    {"field": "water_repellency", "direction": "high"},
    {"field": "breathability", "direction": "high"},
    {"field": "cost_level", "direction": "low"},
    {"field": "lead_time_level", "direction": "low"},
    {"field": "id", "direction": "low"},
]

TIE_BREAKERS_WINTER = [
    {"field": "loft_or_clo", "direction": "high"},
    {"field": "moisture_management", "direction": "high"},
    {"field": "bulk_weight", "direction": "low"},
    {"field": "cost_level", "direction": "low"},
    {"field": "id", "direction": "low"},
]


def _sample_must(rng: random.Random, templates: List[Dict[str, Any]], n_min: int = 2, n_max: int = 4) -> List[Dict[str, Any]]:
    """Sample `n_min..n_max` must constraints without same-field conflicts."""
    n = rng.randint(n_min, n_max)
    sampled: List[Dict[str, Any]] = []
    used_fields: set = set()
    shuffled = templates[:]
    rng.shuffle(shuffled)
    for t in shuffled:
        if t["field"] not in used_fields:
            sampled.append(t)
            used_fields.add(t["field"])
        if len(sampled) >= n:
            break
    return sampled


def _must_text(must_list: List[Dict[str, Any]]) -> str:
    parts = [c.get("reason") or f"{c['field']} {c['op']} {c['value']}" for c in must_list]
    return "; ".join(parts) if parts else "(none)"


def _prefer_text(prefer_list: List[Dict[str, Any]]) -> str:
    parts = [p.get("reason") or p["field"] for p in prefer_list]
    return "; ".join(parts) if parts else "(none)"


def _scenario_stem(scenario: str, must_list: List[Dict[str, Any]], prefer_list: List[Dict[str, Any]]) -> str:
    if scenario == "outdoor_dwr_windbreaker":
        return (
            "Task: select the most suitable fabric for a lightweight outdoor DWR windbreaker.\n"
            f"Hard constraints (must): {_must_text(must_list)}.\n"
            f"Soft preferences (prefer, weighted): {_prefer_text(prefer_list)}.\n"
            "Choose the best option among the four candidates (A/B/C/D)."
        )
    if scenario == "winter_warm_midlayer":
        return (
            "Task: select the most suitable fabric/material option for a winter warm midlayer (synthetic insulation or fleece).\n"
            f"Hard constraints (must): {_must_text(must_list)}.\n"
            f"Soft preferences (prefer, weighted): {_prefer_text(prefer_list)}.\n"
            "Choose the best option among the four candidates (A/B/C/D)."
        )
    raise ValueError(f"Unknown scenario: {scenario}")


def _get_by_path(obj: Mapping[str, Any], path: str) -> Any:
    cur: Any = obj
    for part in path.split("."):
        if not isinstance(cur, Mapping) or part not in cur:
            return None
        cur = cur[part]
    return cur


def _is_cost_or_leadtime_bad(c: Mapping[str, Any]) -> bool:
    cost = c.get("cost_level")
    lead = c.get("lead_time_level")
    return (isinstance(cost, int) and cost >= 4) or (isinstance(lead, int) and lead >= 4)


def _precompute(catalog: List[Dict[str, Any]], rules: Dict[str, Any]) -> List[Dict[str, Any]]:
    out = []
    for c in catalog:
        ok, fails = check_must(c, rules)
        s = score_candidate(c, rules)
        out.append({**c, "_must_ok": ok, "_must_fails": fails, "_score": s})
    return out


def _gen_one_question(
    rng: random.Random,
    scenario: str,
    catalog: List[Dict[str, Any]],
    must_templates: List[Dict[str, Any]],
    prefer_list: List[Dict[str, Any]],
    tie_breakers: List[Dict[str, Any]],
    qid: str,
    gen_seed: int,
    max_tries: int = 300,
) -> Dict[str, Any] | None:
    """Generate one question; return None if no valid 4-option set is found."""
    for _ in range(max_tries):
        must_list = _sample_must(rng, must_templates, n_min=2, n_max=4)
        rules: Dict[str, Any] = {"must": must_list, "prefer": prefer_list, "tie_breakers": tie_breakers}
        pool = _precompute(catalog, rules)

        must_ok = [c for c in pool if c["_must_ok"]]
        must_fail = [c for c in pool if not c["_must_ok"]]
        if len(must_ok) < 3 or len(must_fail) < 1:
            continue

        must_ok_sorted = sorted(must_ok, key=lambda x: float(x["_score"]), reverse=True)
        good_cut = max(5, int(0.25 * len(must_ok_sorted)))
        good_pool = [c for c in must_ok_sorted[:good_cut] if not _is_cost_or_leadtime_bad(c)] or must_ok_sorted[:good_cut]

        median_score = must_ok_sorted[len(must_ok_sorted) // 2]["_score"]
        soft_pool = [c for c in must_ok if c["_score"] <= median_score]
        cost_pool = [c for c in must_ok if _is_cost_or_leadtime_bad(c) and c["_score"] >= median_score]
        if not cost_pool:
            cost_pool = [c for c in must_ok if _is_cost_or_leadtime_bad(c)]
        if not soft_pool:
            soft_pool = must_ok_sorted[-good_cut:]

        if not good_pool or not soft_pool or not cost_pool:
            continue

        good = rng.choice(good_pool)
        good_score = float(good["_score"])

        bad_must = rng.choice(must_fail)
        bad_soft_candidates = [c for c in soft_pool if c["id"] != good["id"]]
        if not bad_soft_candidates:
            continue
        bad_soft = rng.choice(bad_soft_candidates)

        bad_cost_candidates = [c for c in cost_pool if c["id"] not in (good["id"], bad_soft["id"])]
        if not bad_cost_candidates:
            continue
        bad_cost = rng.choice(bad_cost_candidates)

        # Ensure distractors are clearly worse than the correct option.
        if float(bad_soft["_score"]) > good_score - 0.05:
            continue
        if float(bad_cost["_score"]) > good_score - 0.03:
            continue

        keys = ["A", "B", "C", "D"]
        rng.shuffle(keys)

        options: Dict[str, Dict[str, Any]] = {
            keys[0]: {k: v for k, v in good.items() if not k.startswith("_")},
            keys[1]: {k: v for k, v in bad_must.items() if not k.startswith("_")},
            keys[2]: {k: v for k, v in bad_soft.items() if not k.startswith("_")},
            keys[3]: {k: v for k, v in bad_cost.items() if not k.startswith("_")},
        }
        option_tags: Dict[str, List[str]] = {
            keys[0]: ["best"],
            keys[1]: ["must_fail"],
            keys[2]: ["soft_worse"],
            keys[3]: ["cost_leadtime_worse"],
        }

        best_key, scores = pick_best(options, rules)
        if best_key != keys[0]:
            continue

        # Compute the top1-top2 oracle margin.
        sorted_scores = sorted([s for s in scores.values() if s != float("-inf")], reverse=True)
        margin = (sorted_scores[0] - sorted_scores[1]) if len(sorted_scores) >= 2 else 1.0

        stem = _scenario_stem(scenario, must_list, prefer_list)

        return {
            "id": qid,
            "scenario": scenario,
            "stem": stem,
            "options": options,
            "answer": best_key,
            "key_rationales": [],  # can be filled later
            "option_tags": option_tags,
            "meta": {
                "rules_version": 2,
                "gen_seed": gen_seed,
                "oracle_scores": {k: (None if scores[k] == float("-inf") else round(scores[k], 6)) for k in scores},
                "margin": round(margin, 6),
                "must_sample": [m["reason"] for m in must_list],
            },
        }

    return None


def generate_v1_for_scenario(
    rng: random.Random,
    scenario: str,
    catalog: List[Dict[str, Any]],
    n: int,
    qid_prefix: str,
    gen_seed: int,
) -> List[Dict[str, Any]]:
    if scenario == "outdoor_dwr_windbreaker":
        must_templates = MUST_TEMPLATES_OUTDOOR
        prefer_list = PREFER_OUTDOOR
        tie_breakers = TIE_BREAKERS_OUTDOOR
    else:
        must_templates = MUST_TEMPLATES_WINTER
        prefer_list = PREFER_WINTER
        tie_breakers = TIE_BREAKERS_WINTER

    out: List[Dict[str, Any]] = []
    attempts = 0
    max_attempts = n * 5
    while len(out) < n and attempts < max_attempts:
        attempts += 1
        qid = f"{qid_prefix}_{len(out)+1:05d}"
        q = _gen_one_question(rng, scenario, catalog, must_templates, prefer_list, tie_breakers, qid, gen_seed)
        if q:
            out.append(q)
    return out


def compute_meta(questions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute must/prefer/difficulty statistics."""
    must_counter: Counter = Counter()
    scenario_counter: Counter = Counter()
    margin_bins = {"<0.05": 0, "0.05-0.10": 0, "0.10-0.20": 0, ">0.20": 0}

    for q in questions:
        scenario_counter[q["scenario"]] += 1
        for m in q.get("meta", {}).get("must_sample", []):
            must_counter[m] += 1
        margin = q.get("meta", {}).get("margin", 0.0)
        if margin < 0.05:
            margin_bins["<0.05"] += 1
        elif margin < 0.10:
            margin_bins["0.05-0.10"] += 1
        elif margin < 0.20:
            margin_bins["0.10-0.20"] += 1
        else:
            margin_bins[">0.20"] += 1

    return {
        "total": len(questions),
        "by_scenario": dict(scenario_counter),
        "must_distribution": dict(must_counter.most_common()),
        "margin_distribution": margin_bins,
    }


def qc_clean(questions: List[Dict[str, Any]], min_margin: float = 0.05, per_scenario: int = 500) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    QC cleaning:
    1. drop questions with `margin < min_margin` as ambiguous
    2. keep the top `per_scenario` items per scenario
    Returns `(clean_list, qc_stats)`.
    """
    by_scenario: Dict[str, List[Dict[str, Any]]] = {}
    ambiguous_count = 0

    for q in questions:
        margin = q.get("meta", {}).get("margin", 0.0)
        if margin < min_margin:
            ambiguous_count += 1
            continue
        s = q["scenario"]
        if s not in by_scenario:
            by_scenario[s] = []
        by_scenario[s].append(q)

    clean: List[Dict[str, Any]] = []
    kept_by_scenario: Dict[str, int] = {}
    for s, qs in by_scenario.items():
        # Sort by margin descending and keep the top subset.
        qs_sorted = sorted(qs, key=lambda x: x.get("meta", {}).get("margin", 0.0), reverse=True)
        kept = qs_sorted[:per_scenario]
        clean.extend(kept)
        kept_by_scenario[s] = len(kept)

    # Re-index after cleaning.
    for i, q in enumerate(clean):
        q["id"] = f"v1_{i+1:05d}"

    qc_stats = {
        "total_raw": len(questions),
        "ambiguous_dropped": ambiguous_count,
        "kept_by_scenario": kept_by_scenario,
        "total_clean": len(clean),
    }
    return clean, qc_stats


def write_report(meta: Dict[str, Any], qc_stats: Dict[str, Any], out_path: Path) -> None:
    lines = [
        "# Dataset V1 Report",
        "",
        "## 1. Raw Statistics",
        f"- Total questions: {meta['total']}",
        f"- By scenario: {meta['by_scenario']}",
        "",
        "### Must Constraint Distribution",
    ]
    must_dist = meta.get("must_distribution", {})
    if isinstance(must_dist, dict):
        for m, cnt in must_dist.items():
            lines.append(f"- {m}: {cnt}")
    else:
        for item in must_dist:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                lines.append(f"- {item[0]}: {item[1]}")
            else:
                lines.append(f"- {item}")
    lines.append("")
    lines.append("### Margin Distribution (top1 - top2)")
    for k, v in meta["margin_distribution"].items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## 2. QC Cleaning")
    lines.append(f"- Ambiguous dropped (margin < 0.05): {qc_stats['ambiguous_dropped']}")
    lines.append(f"- Kept by scenario: {qc_stats['kept_by_scenario']}")
    lines.append(f"- Total clean: {qc_stats['total_clean']}")
    lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


app = typer.Typer(
    add_completion=False,
    help="Assemble the v1 benchmark release from deterministic rules and run QC cleaning.",
)


@app.command()
def main(
    seed: int = typer.Option(42, help="Random seed"),
    n_outdoor: int = typer.Option(600, "--n-outdoor", help="Number of raw outdoor questions"),
    n_winter: int = typer.Option(600, "--n-winter", help="Number of raw winter questions"),
    clean_per_scenario: int = typer.Option(500, "--clean-per-scenario", help="Number of kept questions per scenario after cleaning"),
    min_margin: float = typer.Option(0.05, "--min-margin", help="Minimum margin threshold (questions below this are treated as ambiguous)"),
    data_dir: Path = typer.Option(Path("data"), help="Data directory"),
    out_dir: Path = typer.Option(Path("outputs"), help="Output directory for the report"),
) -> None:
    rng = random.Random(seed)

    # Read catalogs.
    catalog_outdoor = _read_jsonl(data_dir / "catalog_outdoor.jsonl")
    catalog_winter = _read_jsonl(data_dir / "catalog_winter.jsonl")

    typer.echo(f"Loaded catalog: outdoor={len(catalog_outdoor)}, winter={len(catalog_winter)}")

    # Generate raw questions.
    outdoor_q = generate_v1_for_scenario(rng, "outdoor_dwr_windbreaker", catalog_outdoor, n_outdoor, "outdoor", seed)
    winter_q = generate_v1_for_scenario(rng, "winter_warm_midlayer", catalog_winter, n_winter, "winter", seed)
    all_raw = outdoor_q + winter_q

    typer.echo(f"Generated raw: outdoor={len(outdoor_q)}, winter={len(winter_q)}, total={len(all_raw)}")

    # Write raw questions.
    _write_jsonl(data_dir / "questions_v1.jsonl", all_raw)
    typer.echo(f"Wrote -> {data_dir / 'questions_v1.jsonl'}")

    # Compute metadata.
    meta = compute_meta(all_raw)
    _write_json(data_dir / "questions_v1_meta.json", meta)
    typer.echo(f"Wrote -> {data_dir / 'questions_v1_meta.json'}")

    # Run QC cleaning.
    clean, qc_stats = qc_clean(all_raw, min_margin=min_margin, per_scenario=clean_per_scenario)
    _write_jsonl(data_dir / "questions_v1_clean.jsonl", clean)
    typer.echo(f"Wrote -> {data_dir / 'questions_v1_clean.jsonl'} ({len(clean)} questions)")

    # Write the report.
    report_path = out_dir / "dataset_report.md"
    write_report(meta, qc_stats, report_path)
    typer.echo(f"Wrote -> {report_path}")


if __name__ == "__main__":
    app()

