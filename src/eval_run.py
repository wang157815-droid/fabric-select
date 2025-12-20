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
    retry_on_none: bool = typer.Option(
        True,
        "--retry-on-none/--no-retry-on-none",
        help="当无法抽取 A/B/C/D（pred=None）时，自动用更高的 max_tokens 重试一次（会计入 calls/tokens/latency）。",
    ),
    retry_max_tokens: int = typer.Option(1024, "--retry-max-tokens", help="重试时使用的 max_tokens（仅在 pred=None 时触发）。"),
    progress: bool = typer.Option(True, "--progress/--no-progress", help="显示逐题进度与 ETA"),
    progress_every: int = typer.Option(1, "--progress-every", help="每隔多少题输出一次进度"),
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

    # gpt-5 系列（含 gpt-5-mini）在当前 API 行为下通常不支持自定义 temperature；
    # 为避免“日志记录的 temperature 与实际调用不一致”，这里对 gpt-5* 强制 temperature=1.0。
    if str(getattr(llm, "model", "")).startswith("gpt-5") and float(temperature) != 1.0:
        typer.echo(f"[note] model={llm.model} does not support temperature={temperature}; forcing temperature=1.0")
        temperature = 1.0

    results_csv = out_dir / "results.csv"
    log_jsonl = out_dir / "per_question_log.jsonl"

    for r in range(repeats):
        rng = random.Random(seed + r)
        if n_questions >= len(q_pool):
            batch = list(q_pool)
        else:
            batch = rng.sample(q_pool, n_questions)

        n = len(batch)
        run_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{strategy}_{scenario}_t{temperature}_r{r}"
        t_run0 = time.perf_counter()

        if progress:
            typer.echo(f"[{run_id}] start: strategy={strategy} scenario={scenario} n_questions={n} repeat={r+1}/{repeats}")

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
            retry_info: Optional[Dict[str, Any]] = None
            # 仅对“单智能体”做重试：多智能体内部有 JSON fallback，pick 通常不会是 None
            if (
                strategy in SINGLE_STRATEGIES
                and retry_on_none
                and pred is None
                and int(retry_max_tokens) > int(max_tokens)
            ):
                out2 = run_single_strategy(
                    llm,
                    q,
                    strategy=strategy,
                    temperature=temperature,
                    max_tokens=int(retry_max_tokens),
                    seed=call_seed,
                )
                pred2 = out2.get("pick")
                retry_info = {
                    "attempts": 2,
                    "first_max_tokens": int(max_tokens),
                    "retry_max_tokens": int(retry_max_tokens),
                    "first_pick": pred,
                    "retry_pick": pred2,
                }
                # 合并调用记录：计入总 calls/tokens/latency
                calls1 = out.get("calls") or []
                calls2 = out2.get("calls") or []
                out = {
                    **out,
                    "calls": [*calls1, *calls2],
                    "raw_output": out2.get("raw_output") or out.get("raw_output"),
                }
                pred = pred2
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
                    "retry": retry_info,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )

            if progress and progress_every > 0:
                done = qi + 1
                if (done % progress_every == 0) or (done == n):
                    elapsed = time.perf_counter() - t_run0
                    avg = elapsed / max(1, done)
                    eta = avg * max(0, n - done)
                    acc_so_far = correct / max(1, done)
                    typer.echo(
                        f"[{run_id}] {done}/{n} acc_so_far={acc_so_far:.3f} calls={total_calls} tokens={total_tokens} elapsed_s={elapsed:.1f} eta_s={eta:.1f}"
                    )

        t_run = time.perf_counter() - t_run0
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


