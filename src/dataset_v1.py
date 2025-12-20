"""
dataset_v1: 生成论文级数据集（v1）+ QC 清洗 + meta/report。

用法：
    python -m src.dataset_v1 --seed 42 --n-outdoor 600 --n-winter 600 --clean-per-scenario 500

产出：
    data/questions_v1.jsonl          原始题库（>=1000）
    data/questions_v1_meta.json      must/prefer/难度分布统计
    data/questions_v1_clean.jsonl    清洗后（每场景精确 500）
    outputs/dataset_report.md        唯一答案率、丢弃率、干扰项比例
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
# must 约束模板（每题随机抽 2-3 个组合，保证多样性）
# ─────────────────────────────────────────────────────────────────────────────

MUST_TEMPLATES_OUTDOOR: List[Dict[str, Any]] = [
    {"field": "compliance.pfas_free", "op": "eq", "value": True, "reason": "必须 PFAS-free（合规/可持续）"},
    {"field": "water_repellency", "op": "gte", "value": 4, "reason": "拒水/防泼等级至少 4/5"},
    {"field": "water_repellency", "op": "gte", "value": 3, "reason": "拒水/防泼等级至少 3/5"},
    {"field": "abrasion", "op": "gte", "value": 3, "reason": "耐磨等级至少 3/5（户外使用强度）"},
    {"field": "abrasion", "op": "gte", "value": 4, "reason": "耐磨等级至少 4/5（高强度户外）"},
    {"field": "breathability", "op": "gte", "value": 3, "reason": "透气等级至少 3/5"},
    {"field": "weight_gsm", "op": "lte", "value": 120, "reason": "克重不超过 120gsm（轻量化）"},
    {"field": "weight_gsm", "op": "lte", "value": 150, "reason": "克重不超过 150gsm"},
    {"field": "lead_time_level", "op": "lte", "value": 3, "reason": "交期等级不超过 3（快速上市）"},
    {"field": "cost_level", "op": "lte", "value": 3, "reason": "成本等级不超过 3（预算约束）"},
]

MUST_TEMPLATES_WINTER: List[Dict[str, Any]] = [
    {"field": "care.machine_wash", "op": "eq", "value": True, "reason": "必须可机洗（护理约束）"},
    {"field": "loft_or_clo", "op": "gte", "value": 1.2, "reason": "保暖指标（loft/clo）至少 1.2"},
    {"field": "loft_or_clo", "op": "gte", "value": 1.5, "reason": "保暖指标（loft/clo）至少 1.5（高保暖）"},
    {"field": "moisture_management", "op": "gte", "value": 3, "reason": "排汗/快干能力至少 3/5"},
    {"field": "moisture_management", "op": "gte", "value": 4, "reason": "排汗/快干能力至少 4/5（高运动强度）"},
    {"field": "wind_blocking", "op": "gte", "value": 3, "reason": "抗风等级至少 3/5"},
    {"field": "bulk_weight", "op": "lte", "value": 3, "reason": "臃肿度不超过 3（轻薄要求）"},
    {"field": "compliance.pfas_free", "op": "eq", "value": True, "reason": "必须 PFAS-free（合规/可持续）"},
    {"field": "lead_time_level", "op": "lte", "value": 3, "reason": "交期等级不超过 3"},
    {"field": "cost_level", "op": "lte", "value": 4, "reason": "成本等级不超过 4"},
]

# prefer 保持与 rules_*.json 一致（不做随机抽样，保证评分稳定）
PREFER_OUTDOOR: List[Dict[str, Any]] = [
    {"field": "water_repellency", "weight": 0.20, "direction": "high", "normalization": {"type": "ordinal", "levels": [1,2,3,4,5]}, "reason": "更强拒水/防泼"},
    {"field": "breathability", "weight": 0.18, "direction": "high", "normalization": {"type": "ordinal", "levels": [1,2,3,4,5]}, "reason": "更高透气/舒适"},
    {"field": "abrasion", "weight": 0.15, "direction": "high", "normalization": {"type": "ordinal", "levels": [1,2,3,4,5]}, "reason": "更高耐磨/更耐用"},
    {"field": "handfeel_noise", "weight": 0.10, "direction": "high", "normalization": {"type": "ordinal", "levels": [1,2,3,4,5]}, "reason": "更安静/更好的手感"},
    {"field": "weight_gsm", "weight": 0.10, "direction": "low", "normalization": {"type": "minmax", "min": 60, "max": 180}, "reason": "更轻量"},
    {"field": "cost_level", "weight": 0.15, "direction": "low", "normalization": {"type": "ordinal", "levels": [1,2,3,4,5]}, "reason": "更低成本"},
    {"field": "lead_time_level", "weight": 0.12, "direction": "low", "normalization": {"type": "ordinal", "levels": [1,2,3,4,5]}, "reason": "更短交期"},
]

PREFER_WINTER: List[Dict[str, Any]] = [
    {"field": "loft_or_clo", "weight": 0.30, "direction": "high", "normalization": {"type": "minmax", "min": 0.8, "max": 2.6}, "reason": "更高保暖"},
    {"field": "wind_blocking", "weight": 0.15, "direction": "high", "normalization": {"type": "ordinal", "levels": [1,2,3,4,5]}, "reason": "更强抗风"},
    {"field": "moisture_management", "weight": 0.20, "direction": "high", "normalization": {"type": "ordinal", "levels": [1,2,3,4,5]}, "reason": "更强排汗/快干"},
    {"field": "bulk_weight", "weight": 0.15, "direction": "low", "normalization": {"type": "ordinal", "levels": [1,2,3,4,5]}, "reason": "更轻薄"},
    {"field": "cost_level", "weight": 0.12, "direction": "low", "normalization": {"type": "ordinal", "levels": [1,2,3,4,5]}, "reason": "更低成本"},
    {"field": "lead_time_level", "weight": 0.08, "direction": "low", "normalization": {"type": "ordinal", "levels": [1,2,3,4,5]}, "reason": "更短交期"},
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
    """从模板里随机抽 n_min~n_max 个 must 约束，去重同 field 冲突。"""
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
    return "；".join(parts) if parts else "（无）"


def _prefer_text(prefer_list: List[Dict[str, Any]]) -> str:
    parts = [p.get("reason") or p["field"] for p in prefer_list]
    return "；".join(parts) if parts else "（无）"


def _scenario_stem(scenario: str, must_list: List[Dict[str, Any]], prefer_list: List[Dict[str, Any]]) -> str:
    if scenario == "outdoor_dwr_windbreaker":
        return (
            "任务: 为户外轻量防泼风衣(DWR windbreaker)选择最合适的面料。\n"
            f"硬约束(must): {_must_text(must_list)}。\n"
            f"软偏好(prefer, 加权): {_prefer_text(prefer_list)}。\n"
            "请在 4 个候选(A/B/C/D)中选出最合适的一项。"
        )
    if scenario == "winter_warm_midlayer":
        return (
            "任务: 为冬季保暖中层(合成保暖/抓绒 midlayer)选择最合适的面料/材料方案。\n"
            f"硬约束(must): {_must_text(must_list)}。\n"
            f"软偏好(prefer, 加权): {_prefer_text(prefer_list)}。\n"
            "请在 4 个候选(A/B/C/D)中选出最合适的一项。"
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
    """生成一道题；若多次尝试仍无法构造有效 4 选项，返回 None。"""
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

        # 确保干扰项确实"打不过"正确项（margin 至少 0.05）
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

        # 计算 margin（top1 - top2）
        sorted_scores = sorted([s for s in scores.values() if s != float("-inf")], reverse=True)
        margin = (sorted_scores[0] - sorted_scores[1]) if len(sorted_scores) >= 2 else 1.0

        stem = _scenario_stem(scenario, must_list, prefer_list)

        return {
            "id": qid,
            "scenario": scenario,
            "stem": stem,
            "options": options,
            "answer": best_key,
            "key_rationales": [],  # 可后续补充
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
    """统计 must/prefer/难度分布。"""
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
    QC 清洗：
    1. 丢弃 margin < min_margin（ambiguous）
    2. 每场景取前 per_scenario 条
    返回 (clean_list, qc_stats)
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
        # 按 margin 从大到小排序，取前 per_scenario
        qs_sorted = sorted(qs, key=lambda x: x.get("meta", {}).get("margin", 0.0), reverse=True)
        kept = qs_sorted[:per_scenario]
        clean.extend(kept)
        kept_by_scenario[s] = len(kept)

    # 重新编号
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


app = typer.Typer(add_completion=False, help="生成论文级数据集 v1 + QC 清洗。")


@app.command()
def main(
    seed: int = typer.Option(42, help="随机种子"),
    n_outdoor: int = typer.Option(600, "--n-outdoor", help="outdoor 原始题目数"),
    n_winter: int = typer.Option(600, "--n-winter", help="winter 原始题目数"),
    clean_per_scenario: int = typer.Option(500, "--clean-per-scenario", help="清洗后每场景保留题数"),
    min_margin: float = typer.Option(0.05, "--min-margin", help="最小 margin 阈值（低于此视为 ambiguous）"),
    data_dir: Path = typer.Option(Path("data"), help="数据目录"),
    out_dir: Path = typer.Option(Path("outputs"), help="输出目录（report）"),
) -> None:
    rng = random.Random(seed)

    # 读取 catalog
    catalog_outdoor = _read_jsonl(data_dir / "catalog_outdoor.jsonl")
    catalog_winter = _read_jsonl(data_dir / "catalog_winter.jsonl")

    typer.echo(f"Loaded catalog: outdoor={len(catalog_outdoor)}, winter={len(catalog_winter)}")

    # 生成 raw
    outdoor_q = generate_v1_for_scenario(rng, "outdoor_dwr_windbreaker", catalog_outdoor, n_outdoor, "outdoor", seed)
    winter_q = generate_v1_for_scenario(rng, "winter_warm_midlayer", catalog_winter, n_winter, "winter", seed)
    all_raw = outdoor_q + winter_q

    typer.echo(f"Generated raw: outdoor={len(outdoor_q)}, winter={len(winter_q)}, total={len(all_raw)}")

    # 写 raw
    _write_jsonl(data_dir / "questions_v1.jsonl", all_raw)
    typer.echo(f"Wrote -> {data_dir / 'questions_v1.jsonl'}")

    # 统计 meta
    meta = compute_meta(all_raw)
    _write_json(data_dir / "questions_v1_meta.json", meta)
    typer.echo(f"Wrote -> {data_dir / 'questions_v1_meta.json'}")

    # QC 清洗
    clean, qc_stats = qc_clean(all_raw, min_margin=min_margin, per_scenario=clean_per_scenario)
    _write_jsonl(data_dir / "questions_v1_clean.jsonl", clean)
    typer.echo(f"Wrote -> {data_dir / 'questions_v1_clean.jsonl'} ({len(clean)} questions)")

    # 写 report
    report_path = out_dir / "dataset_report.md"
    write_report(meta, qc_stats, report_path)
    typer.echo(f"Wrote -> {report_path}")


if __name__ == "__main__":
    app()

