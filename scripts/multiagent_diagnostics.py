from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Tuple

import typer


OptionKey = str  # "A"/"B"/"C"/"D"
VALID = {"A", "B", "C", "D"}


def _iter_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def _pairwise_agreement(picks: List[OptionKey]) -> float | None:
    n = len(picks)
    if n < 2:
        return None
    agree = 0
    total = 0
    for i in range(n):
        for j in range(i + 1, n):
            total += 1
            if picks[i] == picks[j]:
                agree += 1
    return agree / total if total else None


def _entropy(picks: List[OptionKey]) -> float | None:
    n = len(picks)
    if n == 0:
        return None
    c = Counter(picks)
    h = 0.0
    for v in c.values():
        p = v / n
        if p > 0:
            h -= p * math.log(p, 2)
    return h


def _mean(vals: List[float]) -> float | None:
    if not vals:
        return None
    return sum(vals) / len(vals)


app = typer.Typer(add_completion=False, help="Offline diagnostics for multi-agent strategies (agreement/entropy/valid-conditional accuracy).")


@app.command()
def main(
    log_jsonl: Path = typer.Option(Path("outputs/per_question_log_main.jsonl"), help="per-question log JSONL"),
    out_csv: Path = typer.Option(Path("outputs/multiagent_diagnostics.csv"), help="output CSV path"),
    strategies: str = typer.Option(
        "voting,weighted_voting,borda,garmentagents_fixed,garmentagents_adaptive",
        help="Comma-separated strategy list (should have agent_decisions).",
    ),
) -> None:
    strategies_set = {s.strip() for s in strategies.split(",") if s.strip()}

    # group -> running lists
    groups: Dict[Tuple[str, str, int], Dict[str, Any]] = defaultdict(lambda: {"total": 0, "valid": 0, "correct_total": 0, "correct_valid": 0, "agree": [], "entropy": [], "gold_share": [], "n_agents": []})

    for rec in _iter_jsonl(log_jsonl):
        strategy = str(rec.get("strategy") or "")
        if strategy not in strategies_set:
            continue
        scenario = str(rec.get("scenario") or "")
        repeat_idx = int(rec.get("repeat_idx", 0) or 0)
        key = (strategy, scenario, repeat_idx)
        g = groups[key]

        g["total"] += 1
        pred = rec.get("pred")
        is_correct = bool(rec.get("is_correct", False))
        if is_correct:
            g["correct_total"] += 1

        if pred in VALID:
            g["valid"] += 1
            if is_correct:
                g["correct_valid"] += 1

        # agent diagnostics (exists for multi-agent strategies)
        decisions = rec.get("agent_decisions") or {}
        if isinstance(decisions, Mapping):
            picks = []
            for d in decisions.values():
                if not isinstance(d, Mapping):
                    continue
                p = d.get("pick")
                if p in VALID:
                    picks.append(str(p))
            if picks:
                g["n_agents"].append(float(len(picks)))
                a = _pairwise_agreement(picks)
                if a is not None:
                    g["agree"].append(float(a))
                h = _entropy(picks)
                if h is not None:
                    g["entropy"].append(float(h))
                gold = rec.get("gold")
                if gold in VALID:
                    g["gold_share"].append(sum(1 for p in picks if p == gold) / len(picks))

    # write csv
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    header = [
        "strategy",
        "scenario",
        "repeat_idx",
        "n_total",
        "n_valid",
        "valid_output_rate",
        "acc_all",
        "acc_valid",
        "mean_n_agents",
        "mean_pairwise_agreement",
        "mean_vote_entropy_bits",
        "mean_gold_vote_share",
    ]
    rows: List[List[str]] = []
    for (strategy, scenario, repeat_idx), g in sorted(groups.items(), key=lambda x: (x[0][0], x[0][1], x[0][2])):
        total = int(g["total"])
        valid = int(g["valid"])
        correct_total = int(g["correct_total"])
        correct_valid = int(g["correct_valid"])
        valid_rate = (valid / total) if total else 0.0
        acc_all = (correct_total / total) if total else 0.0
        acc_valid = (correct_valid / valid) if valid else 0.0

        row = [
            strategy,
            scenario,
            str(repeat_idx),
            str(total),
            str(valid),
            f"{valid_rate:.3f}",
            f"{acc_all:.3f}",
            f"{acc_valid:.3f}",
            f"{(_mean(g['n_agents']) or 0.0):.2f}",
            f"{(_mean(g['agree']) or 0.0):.3f}",
            f"{(_mean(g['entropy']) or 0.0):.3f}",
            f"{(_mean(g['gold_share']) or 0.0):.3f}",
        ]
        rows.append(row)

    with out_csv.open("w", encoding="utf-8", newline="") as f:
        f.write(",".join(header) + "\n")
        for r in rows:
            f.write(",".join(r) + "\n")

    typer.echo(f"Wrote {out_csv} ({len(rows)} rows)")


if __name__ == "__main__":
    app()

