from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Dict, List, Mapping, Tuple

import typer

from .scoring import check_must, load_rules, pick_best, score_candidate

OptionKey = str  # "A"/"B"/"C"/"D"


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def _must_text(rules: Mapping[str, Any]) -> str:
    parts = []
    for c in rules.get("must", []):
        parts.append(c.get("reason") or f"{c.get('field')} {c.get('op')} {c.get('value')}")
    return "；".join(parts) if parts else "（无）"


def _prefer_text(rules: Mapping[str, Any]) -> str:
    parts = []
    for p in rules.get("prefer", []):
        parts.append(p.get("reason") or p.get("field"))
    return "；".join(parts) if parts else "（无）"


def _scenario_stem(scenario: str, rules: Mapping[str, Any]) -> str:
    if scenario == "outdoor_dwr_windbreaker":
        return (
            "任务：为“户外轻量防泼风衣（DWR windbreaker）”选择最合适的面料。\n"
            f"硬约束（must）：{_must_text(rules)}。\n"
            f"软偏好（prefer，加权）：{_prefer_text(rules)}。\n"
            "请在 4 个候选（A/B/C/D）中选出最合适的一项。"
        )
    if scenario == "winter_warm_midlayer":
        return (
            "任务：为“冬季保暖中层（合成保暖/抓绒 midlayer）”选择最合适的面料/材料方案。\n"
            f"硬约束（must）：{_must_text(rules)}。\n"
            f"软偏好（prefer，加权）：{_prefer_text(rules)}。\n"
            "请在 4 个候选（A/B/C/D）中选出最合适的一项。"
        )
    raise ValueError(f"Unknown scenario: {scenario}")


def _is_cost_or_leadtime_bad(c: Mapping[str, Any]) -> bool:
    cost = c.get("cost_level")
    lead = c.get("lead_time_level")
    return (isinstance(cost, int) and cost >= 4) or (isinstance(lead, int) and lead >= 4)


def _value_for_direction(v: Any, direction: str) -> float:
    if v is None:
        return float("-inf") if direction == "high" else float("inf")
    if isinstance(v, bool):
        v = 1.0 if v else 0.0
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(v)
    except Exception:
        # 字符串等：退化为 0
        return 0.0


def _make_key_rationales(
    answer_key: OptionKey,
    options: Mapping[OptionKey, Mapping[str, Any]],
    option_tags: Mapping[OptionKey, List[str]],
    rules: Mapping[str, Any],
) -> List[str]:
    best = options[answer_key]
    rationales: List[str] = []

    ok, _fails = check_must(best, rules)
    if ok:
        rationales.append("正确选项满足所有硬约束（must）。")
    else:
        rationales.append("正确选项在硬约束上风险较低（相对其他候选更符合 must）。")

    # 按权重从高到低挑选“正确选项占优”的 prefer
    prefs = sorted(rules.get("prefer", []), key=lambda x: float(x.get("weight", 0.0)), reverse=True)
    for p in prefs:
        field = p["field"]
        direction = p.get("direction", "high")
        reason = p.get("reason") or field

        best_v = _value_for_direction(best.get(field) if "." not in field else None, direction)
        # 支持嵌套字段
        if "." in field:
            cur: Any = best
            for part in field.split("."):
                cur = cur.get(part) if isinstance(cur, dict) else None
            best_v = _value_for_direction(cur, direction)

        # 找该指标上的“最优项”
        winner = None
        winner_v = None
        for k, c in options.items():
            cur2: Any = c
            if "." in field:
                for part in field.split("."):
                    cur2 = cur2.get(part) if isinstance(cur2, dict) else None
            else:
                cur2 = c.get(field)
            v2 = _value_for_direction(cur2, direction)
            if winner is None:
                winner, winner_v = k, v2
            else:
                if direction == "high" and v2 > winner_v:  # type: ignore[operator]
                    winner, winner_v = k, v2
                if direction == "low" and v2 < winner_v:  # type: ignore[operator]
                    winner, winner_v = k, v2

        if winner == answer_key:
            # 给出可解释的数值提示（若为整数等级则显示 /5）
            show_val = None
            cur3: Any = best
            if "." in field:
                for part in field.split("."):
                    cur3 = cur3.get(part) if isinstance(cur3, dict) else None
            else:
                cur3 = best.get(field)
            show_val = cur3
            if isinstance(show_val, int) and show_val in (1, 2, 3, 4, 5):
                rationales.append(f"在“{reason}”上表现更好（{field}={show_val}/5），综合得分占优。")
            else:
                rationales.append(f"在“{reason}”上表现更好（{field}={show_val}），综合得分占优。")

        if len(rationales) >= 4:
            break

    # 解释三类干扰项
    for k, tags in option_tags.items():
        if "must_fail" in tags:
            ok2, fails = check_must(options[k], rules)
            if not ok2 and fails:
                rationales.append(f"干扰项 {k} 违反硬约束：{fails[0]}。")
            else:
                rationales.append(f"干扰项 {k} 违反硬约束（must）。")
        if "cost_leadtime_worse" in tags:
            c = options[k]
            rationales.append(
                f"干扰项 {k} 性能尚可但成本/交期更差（cost_level={c.get('cost_level')}，lead_time_level={c.get('lead_time_level')}）。"
            )
        if "soft_worse" in tags:
            rationales.append(f"干扰项 {k} 满足 must 但关键软指标明显更弱，综合评分更低。")

    # 去重并裁剪到 3-6 条
    dedup: List[str] = []
    for r in rationales:
        if r not in dedup:
            dedup.append(r)

    return dedup[:6] if len(dedup) >= 3 else (dedup + ["综合权衡后该选项更合适。"])[:3]


def _precompute(catalog: List[Dict[str, Any]], rules: Mapping[str, Any]) -> List[Dict[str, Any]]:
    out = []
    for c in catalog:
        ok, fails = check_must(c, rules)
        s = score_candidate(c, rules)
        out.append({**c, "_must_ok": ok, "_must_fails": fails, "_score": s})
    return out


def _gen_one_question(
    rng: random.Random,
    scenario: str,
    rules: Mapping[str, Any],
    pool: List[Dict[str, Any]],
    qid: str,
    gen_seed: int,
    max_tries: int = 200,
) -> Dict[str, Any]:
    must_ok = [c for c in pool if c["_must_ok"]]
    must_fail = [c for c in pool if not c["_must_ok"]]
    if not must_ok or not must_fail:
        raise RuntimeError("Catalog must contain both must-ok and must-fail candidates.")

    must_ok_sorted = sorted(must_ok, key=lambda x: float(x["_score"]), reverse=True)
    good_cut = max(10, int(0.25 * len(must_ok_sorted)))
    good_pool = must_ok_sorted[:good_cut]

    median_score = must_ok_sorted[len(must_ok_sorted) // 2]["_score"]
    soft_pool = [c for c in must_ok if c["_score"] <= median_score]
    cost_pool = [c for c in must_ok if _is_cost_or_leadtime_bad(c) and c["_score"] >= median_score]

    # 保底：若 pool 不够，再放宽一点
    if not cost_pool:
        cost_pool = [c for c in must_ok if _is_cost_or_leadtime_bad(c)]
    if not soft_pool:
        soft_pool = must_ok_sorted[-good_cut:]

    for _ in range(max_tries):
        good = rng.choice([c for c in good_pool if not _is_cost_or_leadtime_bad(c)] or good_pool)
        good_score = float(good["_score"])

        bad_must = rng.choice(must_fail)
        bad_soft = rng.choice([c for c in soft_pool if c["id"] != good["id"]] or soft_pool)
        bad_cost = rng.choice([c for c in cost_pool if c["id"] not in (good["id"], bad_soft["id"])] or cost_pool)

        # 确保三类干扰项确实“打不过”正确项
        if float(bad_soft["_score"]) > good_score - 0.10:
            continue
        if float(bad_cost["_score"]) > good_score - 0.03:
            continue
        if bad_must["id"] in (good["id"], bad_soft["id"], bad_cost["id"]):
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
            # 纠正：保证“best”确实是标准答案，满足干扰项定义
            continue

        stem = _scenario_stem(scenario, rules)
        key_rationales = _make_key_rationales(best_key, options, option_tags, rules)

        return {
            "id": qid,
            "scenario": scenario,
            "stem": stem,
            "options": options,
            "answer": best_key,
            "key_rationales": key_rationales,
            "option_tags": option_tags,
            "meta": {
                "rules_version": rules.get("version", 1),
                "gen_seed": gen_seed,
                "oracle_scores": {k: (None if scores[k] == float("-inf") else float(scores[k])) for k in scores},
            },
        }

    raise RuntimeError(f"Failed to generate a valid question after {max_tries} tries for {scenario}.")


def generate_questions_for_scenario(
    rng: random.Random,
    scenario: str,
    catalog_path: Path,
    rules_path: Path,
    n: int,
    qid_prefix: str,
    gen_seed: int,
) -> List[Dict[str, Any]]:
    catalog = _read_jsonl(catalog_path)
    rules = load_rules(rules_path)
    pool = _precompute(catalog, rules)

    out: List[Dict[str, Any]] = []
    for i in range(1, n + 1):
        qid = f"{qid_prefix}_{i:05d}"
        out.append(_gen_one_question(rng, scenario, rules, pool, qid=qid, gen_seed=gen_seed))
    return out


app = typer.Typer(add_completion=False, help="从 catalog 生成 MCQ 题库（含规则评分器 ground truth）。")


@app.command()
def main(
    seed: int = typer.Option(42, help="随机种子（保证可复现）"),
    n_outdoor: int = typer.Option(200, "--n-outdoor", help="outdoor 题目数量"),
    n_winter: int = typer.Option(200, "--n-winter", help="winter 题目数量"),
    data_dir: Path = typer.Option(Path("data"), help="数据目录（包含 catalog_* 与输出 questions.jsonl）"),
    config_dir: Path = typer.Option(Path("configs"), help="规则配置目录（rules_outdoor.json / rules_winter.json）"),
) -> None:
    rng = random.Random(seed)

    outdoor = generate_questions_for_scenario(
        rng=rng,
        scenario="outdoor_dwr_windbreaker",
        catalog_path=data_dir / "catalog_outdoor.jsonl",
        rules_path=config_dir / "rules_outdoor.json",
        n=n_outdoor,
        qid_prefix="outdoor",
        gen_seed=seed,
    )
    winter = generate_questions_for_scenario(
        rng=rng,
        scenario="winter_warm_midlayer",
        catalog_path=data_dir / "catalog_winter.jsonl",
        rules_path=config_dir / "rules_winter.json",
        n=n_winter,
        qid_prefix="winter",
        gen_seed=seed,
    )

    all_q = outdoor + winter
    _write_jsonl(data_dir / "questions.jsonl", all_q)

    typer.echo(f"Wrote {len(all_q)} -> {data_dir/'questions.jsonl'} (outdoor={len(outdoor)}, winter={len(winter)})")


if __name__ == "__main__":
    app()


