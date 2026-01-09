#!/usr/bin/env python3
"""
离线消融分析脚本：基于 per_question_log_main.jsonl 中已保存的 5-role agent 输出，
重新计算不同消融变体的准确率/成本，无需额外 API 调用。

支持的消融：
- A1: No Early Stopping（强制跑满所有 agent）
- A2: Static Routing + Early Stop（固定顺序 + 早停）
- A3: 阈值扫描（top1 阈值 / gap 阈值）
- B1: 聚合方式消融（majority / weighted / borda / confidence-weighted）
- B2: #Agents Sweep（K=1..5）
- C1: Role Dropout（移除单个角色）
"""
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple

import typer

app = typer.Typer(add_completion=False, help="离线消融分析")

OptionKey = str
ROLES = ["textile", "technical", "sourcing", "product", "compliance"]
WEIGHTS_OUTDOOR = {"textile": 0.40, "compliance": 0.20, "technical": 0.15, "product": 0.15, "sourcing": 0.10}
WEIGHTS_WINTER = {"textile": 0.35, "technical": 0.20, "product": 0.20, "sourcing": 0.15, "compliance": 0.10}

_RE_RANKING = re.compile(r"ranking\s*:\s*([ABCD])\s*>\s*([ABCD])\s*>\s*([ABCD])\s*>\s*([ABCD])", re.I)


def _get_role_weights(scenario: str) -> Dict[str, float]:
    return WEIGHTS_OUTDOOR if scenario == "outdoor_dwr_windbreaker" else WEIGHTS_WINTER


def _aggregate_majority(decisions: Dict[str, Dict[str, Any]], roles: List[str]) -> Optional[OptionKey]:
    """多数投票"""
    counts: Dict[str, int] = defaultdict(int)
    for r in roles:
        d = decisions.get(r, {})
        pick = d.get("pick")
        if pick in ("A", "B", "C", "D"):
            counts[pick] += 1
    if not counts:
        return None
    return max(counts.keys(), key=lambda k: (counts[k], -ord(k)))


def _aggregate_weighted(decisions: Dict[str, Dict[str, Any]], roles: List[str], weights: Dict[str, float]) -> Tuple[Optional[OptionKey], Dict[str, float]]:
    """加权投票"""
    scores: Dict[str, float] = {k: 0.0 for k in ("A", "B", "C", "D")}
    for r in roles:
        d = decisions.get(r, {})
        pick = d.get("pick")
        if pick in ("A", "B", "C", "D"):
            w = weights.get(r, 1.0)
            conf = float(d.get("confidence", 0.5))
            scores[pick] += w * conf
    if sum(scores.values()) == 0:
        return None, scores
    best = max(scores.keys(), key=lambda k: (scores[k], -ord(k)))
    total = sum(scores.values()) or 1.0
    dist = {k: v / total for k, v in scores.items()}
    return best, dist


def _aggregate_borda(decisions: Dict[str, Dict[str, Any]], roles: List[str], weights: Dict[str, float]) -> Optional[OptionKey]:
    """Borda 计数"""
    points = [3.0, 2.0, 1.0, 0.0]
    scores: Dict[str, float] = {k: 0.0 for k in ("A", "B", "C", "D")}
    for r in roles:
        d = decisions.get(r, {})
        w = weights.get(r, 1.0)
        ranking = None
        for reason in d.get("reasons", [])[:1]:
            m = _RE_RANKING.search(str(reason))
            if m:
                ranking = list(m.groups())
                break
        if ranking and len(set(ranking)) == 4:
            for i, opt in enumerate(ranking):
                scores[opt] += w * points[i]
        else:
            pick = d.get("pick")
            if pick in ("A", "B", "C", "D"):
                scores[pick] += w * points[0]
    if sum(scores.values()) == 0:
        return None
    return max(scores.keys(), key=lambda k: (scores[k], -ord(k)))


def _aggregate_confidence_weighted(decisions: Dict[str, Dict[str, Any]], roles: List[str]) -> Optional[OptionKey]:
    """纯置信度加权（不用角色权重）"""
    scores: Dict[str, float] = {k: 0.0 for k in ("A", "B", "C", "D")}
    for r in roles:
        d = decisions.get(r, {})
        pick = d.get("pick")
        if pick in ("A", "B", "C", "D"):
            conf = float(d.get("confidence", 0.5))
            scores[pick] += conf
    if sum(scores.values()) == 0:
        return None
    return max(scores.keys(), key=lambda k: (scores[k], -ord(k)))


def _top1_gap(dist: Dict[str, float]) -> Tuple[float, float]:
    items = sorted(dist.items(), key=lambda kv: kv[1], reverse=True)
    top1 = items[0][1] if items else 0.0
    top2 = items[1][1] if len(items) > 1 else 0.0
    return top1, top1 - top2


def _count_calls(decisions: Dict[str, Dict[str, Any]], roles: List[str]) -> int:
    return sum(1 for r in roles if decisions.get(r, {}).get("pick") is not None or decisions.get(r))


def _simulate_adaptive(
    decisions: Dict[str, Dict[str, Any]],
    weights: Dict[str, float],
    top1_thresh: float = 0.70,
    gap_thresh: float = 0.25,
    disable_early_stop: bool = False,
) -> Tuple[Optional[OptionKey], int, int]:
    """
    模拟 adaptive 策略：
    - Round 1: 调用权重最高的 3 个角色
    - 若 top1 >= top1_thresh 或 gap >= gap_thresh，则早停
    - 否则 Round 2: 调用剩余 2 个角色
    
    返回：(pick, rounds, calls)
    """
    sorted_roles = sorted(weights.items(), key=lambda kv: kv[1], reverse=True)
    r1_roles = [kv[0] for kv in sorted_roles[:3]]
    r2_roles = [kv[0] for kv in sorted_roles[3:]]
    
    # Round 1
    pick1, dist1 = _aggregate_weighted(decisions, r1_roles, weights)
    top1, gap = _top1_gap(dist1)
    
    if not disable_early_stop and (top1 >= top1_thresh or gap >= gap_thresh):
        return pick1, 1, len(r1_roles)
    
    # Round 2
    all_roles = r1_roles + r2_roles
    pick2, dist2 = _aggregate_weighted(decisions, all_roles, weights)
    return pick2, 2, len(all_roles)


def _load_multi_agent_records(log_jsonl: Path) -> List[Dict[str, Any]]:
    """加载多智能体策略的日志记录（含 agent_decisions）"""
    records = []
    multi_strategies = {"voting", "weighted_voting", "borda", "garmentagents_fixed", "garmentagents_adaptive"}
    with log_jsonl.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if obj.get("strategy") in multi_strategies and obj.get("agent_decisions"):
                    records.append(obj)
            except Exception:
                continue
    return records


@app.command()
def main(
    log_jsonl: Path = typer.Option(..., "--log", help="per_question_log_main.jsonl 路径"),
    out_dir: Path = typer.Option(Path("outputs/figs_ablation"), "--out-dir", help="输出目录"),
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    
    records = _load_multi_agent_records(log_jsonl)
    typer.echo(f"Loaded {len(records)} multi-agent records")
    
    # 按 (strategy, scenario, repeat_idx) 分组
    grouped: Dict[Tuple[str, str, int], List[Dict[str, Any]]] = defaultdict(list)
    for rec in records:
        key = (rec["strategy"], rec["scenario"], int(rec.get("repeat_idx", 0)))
        grouped[key].append(rec)
    
    # ========== A1: No Early Stopping ==========
    typer.echo("\n=== A1: No Early Stopping ===")
    a1_results = []
    for (strategy, scenario, repeat_idx), recs in grouped.items():
        if strategy != "garmentagents_adaptive":
            continue
        weights = _get_role_weights(scenario)
        correct = 0
        total_calls = 0
        for rec in recs:
            decisions = rec.get("agent_decisions", {})
            gold = rec.get("gold")
            # 强制跑满（disable_early_stop=True）
            pick, rounds, calls = _simulate_adaptive(decisions, weights, disable_early_stop=True)
            if pick == gold:
                correct += 1
            total_calls += calls
        n = len(recs)
        acc = correct / n if n > 0 else 0
        avg_calls = total_calls / n if n > 0 else 0
        a1_results.append({
            "variant": "adaptive_no_early_stop",
            "scenario": scenario,
            "repeat_idx": repeat_idx,
            "n": n,
            "correct": correct,
            "accuracy": acc,
            "avg_calls": avg_calls,
        })
        typer.echo(f"  {scenario} r{repeat_idx}: acc={acc:.3f} avg_calls={avg_calls:.2f}")
    
    # 同时计算原始 adaptive 的结果作为对比
    for (strategy, scenario, repeat_idx), recs in grouped.items():
        if strategy != "garmentagents_adaptive":
            continue
        weights = _get_role_weights(scenario)
        correct = 0
        total_calls = 0
        for rec in recs:
            decisions = rec.get("agent_decisions", {})
            gold = rec.get("gold")
            pick, rounds, calls = _simulate_adaptive(decisions, weights, disable_early_stop=False)
            if pick == gold:
                correct += 1
            total_calls += calls
        n = len(recs)
        acc = correct / n if n > 0 else 0
        avg_calls = total_calls / n if n > 0 else 0
        a1_results.append({
            "variant": "adaptive_default",
            "scenario": scenario,
            "repeat_idx": repeat_idx,
            "n": n,
            "correct": correct,
            "accuracy": acc,
            "avg_calls": avg_calls,
        })
    
    # ========== A3: 阈值扫描 ==========
    typer.echo("\n=== A3: Threshold Sweep ===")
    a3_results = []
    thresholds = [(0.5, 0.15), (0.6, 0.20), (0.7, 0.25), (0.8, 0.30), (0.9, 0.35), (1.0, 1.0)]  # (top1_thresh, gap_thresh)
    for (strategy, scenario, repeat_idx), recs in grouped.items():
        if strategy != "garmentagents_adaptive":
            continue
        weights = _get_role_weights(scenario)
        for top1_thresh, gap_thresh in thresholds:
            correct = 0
            total_calls = 0
            for rec in recs:
                decisions = rec.get("agent_decisions", {})
                gold = rec.get("gold")
                pick, rounds, calls = _simulate_adaptive(decisions, weights, top1_thresh=top1_thresh, gap_thresh=gap_thresh)
                if pick == gold:
                    correct += 1
                total_calls += calls
            n = len(recs)
            acc = correct / n if n > 0 else 0
            avg_calls = total_calls / n if n > 0 else 0
            a3_results.append({
                "scenario": scenario,
                "repeat_idx": repeat_idx,
                "top1_thresh": top1_thresh,
                "gap_thresh": gap_thresh,
                "n": n,
                "accuracy": acc,
                "avg_calls": avg_calls,
            })
    
    # ========== B1: 聚合方式消融 ==========
    typer.echo("\n=== B1: Aggregator Ablation ===")
    b1_results = []
    # 使用 garmentagents_fixed 的数据（所有 5 个 agent 都有输出）
    for (strategy, scenario, repeat_idx), recs in grouped.items():
        if strategy != "garmentagents_fixed":
            continue
        weights = _get_role_weights(scenario)
        all_roles = ROLES
        
        for agg_name, agg_fn in [
            ("majority", lambda d: _aggregate_majority(d, all_roles)),
            ("weighted", lambda d: _aggregate_weighted(d, all_roles, weights)[0]),
            ("borda", lambda d: _aggregate_borda(d, all_roles, weights)),
            ("confidence", lambda d: _aggregate_confidence_weighted(d, all_roles)),
        ]:
            correct = 0
            for rec in recs:
                decisions = rec.get("agent_decisions", {})
                gold = rec.get("gold")
                pick = agg_fn(decisions)
                if pick == gold:
                    correct += 1
            n = len(recs)
            acc = correct / n if n > 0 else 0
            b1_results.append({
                "aggregator": agg_name,
                "scenario": scenario,
                "repeat_idx": repeat_idx,
                "n": n,
                "accuracy": acc,
            })
            typer.echo(f"  {agg_name} {scenario} r{repeat_idx}: acc={acc:.3f}")
    
    # ========== B2: #Agents Sweep ==========
    typer.echo("\n=== B2: #Agents Sweep ===")
    b2_results = []
    for (strategy, scenario, repeat_idx), recs in grouped.items():
        if strategy != "garmentagents_fixed":
            continue
        weights = _get_role_weights(scenario)
        sorted_roles = sorted(weights.items(), key=lambda kv: kv[1], reverse=True)
        
        for k in range(1, 6):
            top_k_roles = [r for r, _ in sorted_roles[:k]]
            correct = 0
            for rec in recs:
                decisions = rec.get("agent_decisions", {})
                gold = rec.get("gold")
                pick = _aggregate_majority(decisions, top_k_roles)
                if pick == gold:
                    correct += 1
            n = len(recs)
            acc = correct / n if n > 0 else 0
            b2_results.append({
                "k_agents": k,
                "scenario": scenario,
                "repeat_idx": repeat_idx,
                "n": n,
                "accuracy": acc,
                "roles": ",".join(top_k_roles),
            })
            typer.echo(f"  K={k} {scenario} r{repeat_idx}: acc={acc:.3f}")
    
    # ========== C1: Role Dropout ==========
    typer.echo("\n=== C1: Role Dropout ===")
    c1_results = []
    for (strategy, scenario, repeat_idx), recs in grouped.items():
        if strategy != "garmentagents_fixed":
            continue
        weights = _get_role_weights(scenario)
        
        # Baseline: all roles
        correct_baseline = 0
        for rec in recs:
            decisions = rec.get("agent_decisions", {})
            gold = rec.get("gold")
            pick, _ = _aggregate_weighted(decisions, ROLES, weights)
            if pick == gold:
                correct_baseline += 1
        n = len(recs)
        acc_baseline = correct_baseline / n if n > 0 else 0
        c1_results.append({
            "dropped_role": "none",
            "scenario": scenario,
            "repeat_idx": repeat_idx,
            "n": n,
            "accuracy": acc_baseline,
        })
        
        # Drop each role
        for drop_role in ROLES:
            remaining_roles = [r for r in ROLES if r != drop_role]
            correct = 0
            for rec in recs:
                decisions = rec.get("agent_decisions", {})
                gold = rec.get("gold")
                pick, _ = _aggregate_weighted(decisions, remaining_roles, weights)
                if pick == gold:
                    correct += 1
            acc = correct / n if n > 0 else 0
            c1_results.append({
                "dropped_role": drop_role,
                "scenario": scenario,
                "repeat_idx": repeat_idx,
                "n": n,
                "accuracy": acc,
            })
            typer.echo(f"  drop={drop_role} {scenario} r{repeat_idx}: acc={acc:.3f} (baseline={acc_baseline:.3f})")
    
    # ========== 保存结果 ==========
    import csv
    
    def save_csv(data: List[Dict], filename: str):
        if not data:
            return
        path = out_dir / filename
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(data[0].keys()))
            writer.writeheader()
            writer.writerows(data)
        typer.echo(f"Wrote {path}")
    
    save_csv(a1_results, "ablation_a1_no_early_stop.csv")
    save_csv(a3_results, "ablation_a3_threshold_sweep.csv")
    save_csv(b1_results, "ablation_b1_aggregator.csv")
    save_csv(b2_results, "ablation_b2_agents_sweep.csv")
    save_csv(c1_results, "ablation_c1_role_dropout.csv")
    
    # ========== 生成汇总报告 ==========
    report_lines = ["# Ablation Study Results (Offline)\n"]
    report_lines.append("基于 `per_question_log_main.jsonl` 中已保存的 5-role agent 输出进行离线计算。\n")
    
    report_lines.append("## A1: No Early Stopping\n")
    report_lines.append("| Variant | Scenario | Repeat | N | Accuracy | Avg Calls |")
    report_lines.append("|---------|----------|--------|---|----------|-----------|")
    for r in sorted(a1_results, key=lambda x: (x["variant"], x["scenario"], x["repeat_idx"])):
        report_lines.append(f"| {r['variant']} | {r['scenario']} | {r['repeat_idx']} | {r['n']} | {r['accuracy']:.3f} | {r['avg_calls']:.2f} |")
    report_lines.append("")
    
    report_lines.append("## A3: Threshold Sweep\n")
    report_lines.append("| Scenario | Repeat | Top1 Thresh | Gap Thresh | Accuracy | Avg Calls |")
    report_lines.append("|----------|--------|-------------|------------|----------|-----------|")
    for r in sorted(a3_results, key=lambda x: (x["scenario"], x["repeat_idx"], x["top1_thresh"])):
        report_lines.append(f"| {r['scenario']} | {r['repeat_idx']} | {r['top1_thresh']:.2f} | {r['gap_thresh']:.2f} | {r['accuracy']:.3f} | {r['avg_calls']:.2f} |")
    report_lines.append("")
    
    report_lines.append("## B1: Aggregator Ablation\n")
    report_lines.append("| Aggregator | Scenario | Repeat | Accuracy |")
    report_lines.append("|------------|----------|--------|----------|")
    for r in sorted(b1_results, key=lambda x: (x["aggregator"], x["scenario"], x["repeat_idx"])):
        report_lines.append(f"| {r['aggregator']} | {r['scenario']} | {r['repeat_idx']} | {r['accuracy']:.3f} |")
    report_lines.append("")
    
    report_lines.append("## B2: #Agents Sweep\n")
    report_lines.append("| K | Scenario | Repeat | Accuracy | Roles |")
    report_lines.append("|---|----------|--------|----------|-------|")
    for r in sorted(b2_results, key=lambda x: (x["k_agents"], x["scenario"], x["repeat_idx"])):
        report_lines.append(f"| {r['k_agents']} | {r['scenario']} | {r['repeat_idx']} | {r['accuracy']:.3f} | {r['roles']} |")
    report_lines.append("")
    
    report_lines.append("## C1: Role Dropout\n")
    report_lines.append("| Dropped Role | Scenario | Repeat | Accuracy |")
    report_lines.append("|--------------|----------|--------|----------|")
    for r in sorted(c1_results, key=lambda x: (x["dropped_role"], x["scenario"], x["repeat_idx"])):
        report_lines.append(f"| {r['dropped_role']} | {r['scenario']} | {r['repeat_idx']} | {r['accuracy']:.3f} |")
    report_lines.append("")
    
    report_path = out_dir / "ablation_report.md"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")
    typer.echo(f"Wrote {report_path}")
    
    # ========== 生成可视化图表 ==========
    try:
        import matplotlib.pyplot as plt
        import numpy as np
        
        plt.rcParams["font.family"] = "DejaVu Sans"
        plt.rcParams["axes.unicode_minus"] = False
        
        # --- B1: Aggregator Comparison Bar Chart ---
        if b1_results:
            typer.echo("\nGenerating B1 aggregator bar chart...")
            agg_names = ["majority", "weighted", "borda", "confidence"]
            agg_means = {}
            for agg in agg_names:
                vals = [r["accuracy"] for r in b1_results if r["aggregator"] == agg]
                agg_means[agg] = np.mean(vals) if vals else 0
            
            fig, ax = plt.subplots(figsize=(8, 5))
            x = np.arange(len(agg_names))
            bars = ax.bar(x, [agg_means[a] for a in agg_names], color=["#4e79a7", "#f28e2b", "#e15759", "#76b7b2"])
            ax.set_xticks(x)
            ax.set_xticklabels(agg_names, fontsize=11)
            ax.set_ylabel("Accuracy", fontsize=12)
            ax.set_title("Aggregator Ablation (5 agents, mean across repeats)", fontsize=13)
            ax.set_ylim(0, 0.6)
            for bar in bars:
                h = bar.get_height()
                ax.annotate(f"{h:.3f}", xy=(bar.get_x() + bar.get_width() / 2, h),
                            ha="center", va="bottom", fontsize=10)
            plt.tight_layout()
            fig.savefig(out_dir / "ablation_b1_aggregator.png", dpi=150)
            plt.close(fig)
            typer.echo(f"Wrote {out_dir / 'ablation_b1_aggregator.png'}")
        
        # --- B2: #Agents Sweep Line Chart ---
        if b2_results:
            typer.echo("Generating B2 agents sweep line chart...")
            fig, ax = plt.subplots(figsize=(8, 5))
            for scenario in ["outdoor_dwr_windbreaker", "winter_warm_midlayer"]:
                ks = sorted(set(r["k_agents"] for r in b2_results if r["scenario"] == scenario))
                means = []
                for k in ks:
                    vals = [r["accuracy"] for r in b2_results if r["scenario"] == scenario and r["k_agents"] == k]
                    means.append(np.mean(vals) if vals else 0)
                label = "outdoor" if "outdoor" in scenario else "winter"
                ax.plot(ks, means, marker="o", linewidth=2, markersize=8, label=label)
            ax.set_xlabel("Number of Agents (K)", fontsize=12)
            ax.set_ylabel("Accuracy", fontsize=12)
            ax.set_title("#Agents Sweep (majority voting)", fontsize=13)
            ax.set_xticks([1, 2, 3, 4, 5])
            ax.set_ylim(0, 0.55)
            ax.legend(loc="lower right", fontsize=11)
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            fig.savefig(out_dir / "ablation_b2_agents_sweep.png", dpi=150)
            plt.close(fig)
            typer.echo(f"Wrote {out_dir / 'ablation_b2_agents_sweep.png'}")
        
        # --- C1: Role Dropout Bar Chart ---
        if c1_results:
            typer.echo("Generating C1 role dropout bar chart...")
            roles_to_plot = ["none", "textile", "technical", "sourcing", "product", "compliance"]
            role_means = {}
            for role in roles_to_plot:
                vals = [r["accuracy"] for r in c1_results if r["dropped_role"] == role]
                role_means[role] = np.mean(vals) if vals else 0
            
            fig, ax = plt.subplots(figsize=(9, 5))
            x = np.arange(len(roles_to_plot))
            colors = ["#59a14f"] + ["#e15759"] * 5  # green for baseline, red for drops
            bars = ax.bar(x, [role_means[r] for r in roles_to_plot], color=colors)
            ax.set_xticks(x)
            ax.set_xticklabels(["baseline\n(all 5)"] + [f"drop\n{r}" for r in roles_to_plot[1:]], fontsize=10)
            ax.set_ylabel("Accuracy", fontsize=12)
            ax.set_title("Role Dropout Ablation (weighted voting)", fontsize=13)
            ax.set_ylim(0, 0.5)
            ax.axhline(y=role_means["none"], color="#59a14f", linestyle="--", alpha=0.5)
            for bar in bars:
                h = bar.get_height()
                ax.annotate(f"{h:.3f}", xy=(bar.get_x() + bar.get_width() / 2, h),
                            ha="center", va="bottom", fontsize=9)
            plt.tight_layout()
            fig.savefig(out_dir / "ablation_c1_role_dropout.png", dpi=150)
            plt.close(fig)
            typer.echo(f"Wrote {out_dir / 'ablation_c1_role_dropout.png'}")
        
        # --- A1: Early Stop Comparison ---
        if a1_results:
            typer.echo("Generating A1 early stop comparison...")
            fig, axes = plt.subplots(1, 2, figsize=(12, 5))
            
            # Accuracy comparison
            ax = axes[0]
            variants = ["adaptive_default", "adaptive_no_early_stop"]
            variant_labels = ["With Early Stop", "No Early Stop"]
            means = []
            for v in variants:
                vals = [r["accuracy"] for r in a1_results if r["variant"] == v]
                means.append(np.mean(vals) if vals else 0)
            bars = ax.bar(variant_labels, means, color=["#4e79a7", "#f28e2b"])
            ax.set_ylabel("Accuracy", fontsize=12)
            ax.set_title("Accuracy", fontsize=13)
            ax.set_ylim(0, 0.5)
            for bar in bars:
                h = bar.get_height()
                ax.annotate(f"{h:.3f}", xy=(bar.get_x() + bar.get_width() / 2, h),
                            ha="center", va="bottom", fontsize=10)
            
            # Calls comparison
            ax = axes[1]
            call_means = []
            for v in variants:
                vals = [r["avg_calls"] for r in a1_results if r["variant"] == v]
                call_means.append(np.mean(vals) if vals else 0)
            bars = ax.bar(variant_labels, call_means, color=["#4e79a7", "#f28e2b"])
            ax.set_ylabel("Avg API Calls", fontsize=12)
            ax.set_title("API Calls per Question", fontsize=13)
            ax.set_ylim(0, 6)
            for bar in bars:
                h = bar.get_height()
                ax.annotate(f"{h:.2f}", xy=(bar.get_x() + bar.get_width() / 2, h),
                            ha="center", va="bottom", fontsize=10)
            
            fig.suptitle("Early Stopping Ablation (Adaptive Strategy)", fontsize=14, y=1.02)
            plt.tight_layout()
            fig.savefig(out_dir / "ablation_a1_early_stop.png", dpi=150)
            plt.close(fig)
            typer.echo(f"Wrote {out_dir / 'ablation_a1_early_stop.png'}")
        
        # --- A3: Threshold Sweep Heatmap ---
        if a3_results:
            typer.echo("Generating A3 threshold sweep chart...")
            fig, ax = plt.subplots(figsize=(8, 5))
            thresholds_list = [(0.5, 0.15), (0.6, 0.20), (0.7, 0.25), (0.8, 0.30), (0.9, 0.35), (1.0, 1.0)]
            thresh_labels = [f"({t[0]:.1f}, {t[1]:.2f})" for t in thresholds_list]
            
            acc_means = []
            call_means = []
            for t1, g in thresholds_list:
                acc_vals = [r["accuracy"] for r in a3_results if abs(r["top1_thresh"] - t1) < 0.01 and abs(r["gap_thresh"] - g) < 0.01]
                call_vals = [r["avg_calls"] for r in a3_results if abs(r["top1_thresh"] - t1) < 0.01 and abs(r["gap_thresh"] - g) < 0.01]
                acc_means.append(np.mean(acc_vals) if acc_vals else 0)
                call_means.append(np.mean(call_vals) if call_vals else 0)
            
            x = np.arange(len(thresh_labels))
            width = 0.35
            bars1 = ax.bar(x - width/2, acc_means, width, label="Accuracy", color="#4e79a7")
            ax2 = ax.twinx()
            bars2 = ax2.bar(x + width/2, call_means, width, label="Avg Calls", color="#f28e2b")
            
            ax.set_xticks(x)
            ax.set_xticklabels(thresh_labels, rotation=45, ha="right", fontsize=9)
            ax.set_xlabel("(Top1 Thresh, Gap Thresh)", fontsize=11)
            ax.set_ylabel("Accuracy", fontsize=12, color="#4e79a7")
            ax2.set_ylabel("Avg API Calls", fontsize=12, color="#f28e2b")
            ax.set_ylim(0, 0.5)
            ax2.set_ylim(0, 5.5)
            ax.legend(loc="upper left")
            ax2.legend(loc="upper right")
            ax.set_title("Threshold Sweep (Adaptive Strategy)", fontsize=13)
            plt.tight_layout()
            fig.savefig(out_dir / "ablation_a3_threshold_sweep.png", dpi=150)
            plt.close(fig)
            typer.echo(f"Wrote {out_dir / 'ablation_a3_threshold_sweep.png'}")
        
    except ImportError:
        typer.echo("matplotlib not available, skipping plot generation")
    
    typer.echo("\nDone!")


if __name__ == "__main__":
    app()

