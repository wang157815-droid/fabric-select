from __future__ import annotations

import csv
import json
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

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
    # 为避免“同一个 csv 文件混入不同列集合导致错位”，若已存在文件，则要求 header 与 row keys 一致。
    if file_exists:
        with path.open("r", newline="", encoding="utf-8") as rf:
            reader = csv.reader(rf)
            header = next(reader, None) or []
        if header and set(header) != set(row.keys()):
            raise ValueError(
                f"CSV header mismatch for {path}. "
                f"Existing={header}, new={list(row.keys())}. "
                "Please use a new --results-name (recommended for main experiments)."
            )
        fieldnames = header if header else list(row.keys())
    else:
        fieldnames = list(row.keys())

    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(fieldnames))
        if not file_exists:
            writer.writeheader()
        # 补齐缺失 key，避免 DictWriter 报错
        out_row = {k: row.get(k) for k in fieldnames}
        writer.writerow(out_row)


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

def _run_key(
    *,
    questions_path: Path,
    strategy: str,
    scenario: str,
    temperature: float,
    repeat_idx: int,
    n_questions: int,
    seed: int,
    max_tokens: int,
    retry_on_none: bool,
    retry_max_tokens: int,
    model: str,
) -> Tuple[str, str, str, float, int, int, int, int, bool, int, str]:
    return (
        str(questions_path),
        strategy,
        scenario,
        float(temperature),
        int(repeat_idx),
        int(n_questions),
        int(seed),
        int(max_tokens),
        bool(retry_on_none),
        int(retry_max_tokens),
        str(model),
    )


def _load_existing_keys(results_csv: Path) -> set[Tuple[str, str, str, float, int, int, int, int, bool, int, str]]:
    if not results_csv.exists():
        return set()
    keys: set[Tuple[str, str, str, float, int, int, int, int, bool, int, str]] = set()
    with results_csv.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                keys.add(
                    _run_key(
                        questions_path=Path(row.get("questions_path") or ""),
                        strategy=str(row.get("strategy")),
                        scenario=str(row.get("scenario")),
                        temperature=float(row.get("temperature")),
                        repeat_idx=int(row.get("repeat_idx")),
                        n_questions=int(row.get("n_questions")),
                        seed=int(row.get("seed")),
                        max_tokens=int(row.get("max_tokens")),
                        retry_on_none=str(row.get("retry_on_none")).lower() in ("1", "true", "yes"),
                        retry_max_tokens=int(row.get("retry_max_tokens")),
                        model=str(row.get("model")),
                    )
                )
            except Exception:
                # 兼容旧 results.csv（缺字段/类型不一致），直接跳过不计入去重
                continue
    return keys


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
    results_name: str = typer.Option("results.csv", "--results-name", help="结果 CSV 文件名（例如 results_main.csv）"),
    log_name: str = typer.Option("per_question_log.jsonl", "--log-name", help="逐题日志 JSONL 文件名（例如 per_question_log_main.jsonl）"),
    skip_existing: bool = typer.Option(
        False,
        "--skip-existing/--no-skip-existing",
        help="若 results 文件中已存在相同配置(questions_path/strategy/scenario/t/repeat/n/seed/max_tokens/重试参数/model)的记录，则跳过该 repeat。",
    ),
    log_messages: bool = typer.Option(
        False,
        "--log-messages/--no-log-messages",
        help="是否在 per_question_log 中记录完整 messages（会显著增大体积；主实验建议关闭）。",
    ),
    abort_on_llm_error: bool = typer.Option(
        True,
        "--abort-on-llm-error/--no-abort-on-llm-error",
        help="若任意一次调用返回 [LLM_ERROR]，立即中止本次 run（避免 tokens=0 的假结果污染主实验）。",
    ),
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

    results_csv = out_dir / results_name
    log_jsonl = out_dir / log_name
    existing_keys = _load_existing_keys(results_csv) if skip_existing else set()

    for r in range(repeats):
        rng = random.Random(seed + r)
        if n_questions >= len(q_pool):
            batch = list(q_pool)
        else:
            batch = rng.sample(q_pool, n_questions)

        n = len(batch)
        if skip_existing:
            k = _run_key(
                questions_path=questions_path,
                strategy=strategy,
                scenario=scenario,
                temperature=temperature,
                repeat_idx=r,
                n_questions=n,
                seed=seed,
                max_tokens=max_tokens,
                retry_on_none=retry_on_none,
                retry_max_tokens=retry_max_tokens,
                model=str(llm.model),
            )
            if k in existing_keys:
                typer.echo(f"[skip] existing result found for strategy={strategy} scenario={scenario} t={temperature} r={r} n={n} seed={seed} -> {results_csv}")
                continue
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
            if not log_messages:
                # 主实验默认不记录完整 prompt messages（体积会爆炸）；需要调试时可开 --log-messages
                for c in calls:
                    if isinstance(c, dict) and "messages" in c:
                        c.pop("messages", None)

            llm_err_texts = [
                str(c.get("response_text") or "")
                for c in calls
                if isinstance(c, dict) and str(c.get("response_text") or "").strip().startswith("[LLM_ERROR]")
            ]
            llm_error = bool(llm_err_texts)
            total_calls += len(calls)
            total_latency += _sum_latency(calls)
            usage_sum = _sum_usage(calls)
            total_tokens += usage_sum["total_tokens"]

            _append_jsonl(
                log_jsonl,
                {
                    "run_id": run_id,
                    "questions_path": str(questions_path),
                    "strategy": strategy,
                    "scenario": scenario,
                    "temperature": temperature,
                    "repeat_idx": r,
                    "question_id": qid,
                    "gold": gold,
                    "pred": pred,
                    "is_correct": is_correct,
                    "llm_error": llm_error,
                    "llm_error_preview": (llm_err_texts[0][:240] if llm_err_texts else None),
                    "calls": calls,
                    "usage_sum": usage_sum,
                    "latency_sum_s": _sum_latency(calls),
                    "raw_output": out.get("raw_output"),
                    "agent_decisions": out.get("agent_decisions"),
                    "aggregation": out.get("aggregation"),
                    "retry": retry_info,
                    "max_tokens": int(max_tokens),
                    "retry_on_none": bool(retry_on_none),
                    "retry_max_tokens": int(retry_max_tokens),
                    "log_messages": bool(log_messages),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )

            if llm_error and abort_on_llm_error:
                typer.echo(f"[{run_id}] abort: LLM_ERROR detected (example): {llm_err_texts[0][:160]}")
                raise typer.Exit(code=2)

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
            "questions_path": str(questions_path),
            "strategy": strategy,
            "scenario": scenario,
            "temperature": temperature,
            "repeat_idx": r,
            "n_questions": n,
            "seed": int(seed),
            "max_tokens": int(max_tokens),
            "retry_on_none": bool(retry_on_none),
            "retry_max_tokens": int(retry_max_tokens),
            "log_messages": bool(log_messages),
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


