from __future__ import annotations

import csv
import json
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

import typer

from .llm_client import OpenAIClient
from .strategies_multi import run_multi_strategy
from .strategies_single import run_single_strategy

SINGLE_STRATEGIES = {"zero_shot", "few_shot", "cot_few_shot", "self_reflection", "fashionprompt"}
MULTI_STRATEGIES = {"voting", "weighted_voting", "borda", "garmentagents_fixed", "garmentagents_adaptive"}


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _append_jsonl(path: Path, obj: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _append_csv(path: Path, row: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def _sum_usage(calls: List[Mapping[str, Any]]) -> Dict[str, int]:
    total_in = 0
    total_out = 0
    total_all = 0
    for c in calls:
        u = c.get("usage") or {}
        total_in += int(u.get("input_tokens") or 0)
        total_out += int(u.get("output_tokens") or 0)
        total_all += int(u.get("total_tokens") or 0)
    return {"input_tokens": total_in, "output_tokens": total_out, "total_tokens": total_all}


def _sum_latency(calls: List[Mapping[str, Any]]) -> float:
    return float(sum(float(c.get("latency_s") or 0.0) for c in calls))


app = typer.Typer(add_completion=False, help="运行 LLM 策略评测，输出 results.csv 与 per_question_log.jsonl。")


@app.command()
def main(
    strategy: str = typer.Option(..., help=f"策略名：单智能体={sorted(SINGLE_STRATEGIES)}；多智能体={sorted(MULTI_STRATEGIES)}"),
    scenario: str = typer.Option("outdoor_dwr_windbreaker", help="场景：outdoor_dwr_windbreaker / winter_warm_midlayer"),
    temperature: float = typer.Option(0.6, help="采样温度"),
    repeats: int = typer.Option(2, help="重复次数"),
    n_questions: int = typer.Option(50, "--n-questions", help="每次重复抽取题目数"),
    seed: int = typer.Option(123, help="抽题随机种子"),
    max_tokens: int = typer.Option(512, help="单次调用最大输出 tokens"),
    questions_path: Path = typer.Option(Path("data/questions.jsonl"), help="题库路径（jsonl）"),
    out_dir: Path = typer.Option(Path("outputs"), help="输出目录（results.csv + per_question_log.jsonl）"),
) -> None:
    if strategy not in SINGLE_STRATEGIES and strategy not in MULTI_STRATEGIES:
        raise typer.BadParameter(f"Unknown strategy: {strategy}")

    all_q = _read_jsonl(questions_path)
    q_pool = [q for q in all_q if str(q.get("scenario")) == scenario]
    if not q_pool:
        raise typer.BadParameter(f"No questions for scenario={scenario}. Check {questions_path}")

    llm = OpenAIClient()

    results_csv = out_dir / "results.csv"
    log_jsonl = out_dir / "per_question_log.jsonl"

    for r in range(repeats):
        rng = random.Random(seed + r)
        if n_questions >= len(q_pool):
            batch = list(q_pool)
        else:
            batch = rng.sample(q_pool, n_questions)

        run_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{strategy}_{scenario}_t{temperature}_r{r}"
        t_run0 = time.perf_counter()

        correct = 0
        total_calls = 0
        total_latency = 0.0
        total_tokens = 0

        for qi, q in enumerate(batch):
            qid = q.get("id")
            gold = q.get("answer")

            # 给 LLM 的 seed：保证“同 repeat 内稳定”，不同题也不同
            call_seed: Optional[int] = (seed + r * 100_000 + qi) if seed is not None else None

            if strategy in SINGLE_STRATEGIES:
                out = run_single_strategy(llm, q, strategy=strategy, temperature=temperature, max_tokens=max_tokens, seed=call_seed)
            else:
                out = run_multi_strategy(llm, q, strategy=strategy, temperature=temperature, max_tokens=max_tokens, seed=call_seed)

            pred = out.get("pick")
            is_correct = bool(pred == gold)
            correct += 1 if is_correct else 0

            calls = out.get("calls") or []
            total_calls += len(calls)
            total_latency += _sum_latency(calls)
            usage_sum = _sum_usage(calls)
            total_tokens += usage_sum["total_tokens"]

            _append_jsonl(
                log_jsonl,
                {
                    "run_id": run_id,
                    "strategy": strategy,
                    "scenario": scenario,
                    "temperature": temperature,
                    "repeat_idx": r,
                    "question_id": qid,
                    "gold": gold,
                    "pred": pred,
                    "is_correct": is_correct,
                    "calls": calls,
                    "usage_sum": usage_sum,
                    "latency_sum_s": _sum_latency(calls),
                    "raw_output": out.get("raw_output"),
                    "agent_decisions": out.get("agent_decisions"),
                    "aggregation": out.get("aggregation"),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )

        t_run = time.perf_counter() - t_run0
        n = len(batch)
        acc = correct / max(1, n)
        row = {
            "run_id": run_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "strategy": strategy,
            "scenario": scenario,
            "temperature": temperature,
            "repeat_idx": r,
            "n_questions": n,
            "correct": correct,
            "accuracy": acc,
            "model": llm.model,
            "total_calls": total_calls,
            "total_tokens": total_tokens,
            "total_latency_s": round(total_latency, 6),
            "avg_latency_s": round(total_latency / max(1, n), 6),
            "avg_tokens": round(total_tokens / max(1, n), 3),
            "avg_calls": round(total_calls / max(1, n), 3),
            "wall_time_s": round(t_run, 6),
        }
        _append_csv(results_csv, row)

        typer.echo(
            f"[{run_id}] acc={acc:.3f} correct={correct}/{n} calls={total_calls} tokens={total_tokens} latency_s={total_latency:.2f} wall_s={t_run:.2f}"
        )


if __name__ == "__main__":
    app()


