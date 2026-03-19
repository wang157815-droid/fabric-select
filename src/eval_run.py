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
from .strategies_non_llm import NON_LLM_STRATEGIES, run_non_llm_strategy
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
    # Prevent column misalignment when appending to an existing CSV file.
    # If the file already exists, require the header to match the new row keys.
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
        # Fill missing keys to keep DictWriter happy.
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


app = typer.Typer(add_completion=False, help="Run strategy evaluation and write results.csv plus per_question_log.jsonl.")

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
                # Be tolerant of older results.csv files with missing or mismatched fields.
                continue
    return keys


def _load_completed_qids(
    log_jsonl: Path,
    questions_path: Path,
    strategy: str,
    scenario: str,
    temperature: float,
    repeat_idx: int,
    seed: int,
) -> set[str]:
    """
    Read completed question IDs from `per_question_log.jsonl`.

    Match records by `questions_path + strategy/scenario/temperature/repeat_idx`
    to support both old and new log formats.
    """
    if not log_jsonl.exists():
        return set()
    done: set[str] = set()
    with log_jsonl.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                # Match explicit fields instead of a run_id prefix.
                if (
                    str(obj.get("questions_path")) == str(questions_path)
                    and str(obj.get("strategy")) == strategy
                    and str(obj.get("scenario")) == scenario
                    and float(obj.get("temperature", -1)) == float(temperature)
                    and int(obj.get("repeat_idx", -1)) == int(repeat_idx)
                ):
                    qid = str(obj.get("question_id") or "")
                    # Only treat successfully parsed A/B/C/D predictions as completed
                    # so failed `pred=None` cases are not skipped during resume.
                    pred = str(obj.get("pred") or "").strip()
                    if qid and pred in ("A", "B", "C", "D"):
                        done.add(qid)
            except Exception:
                continue
    return done


def _summarize_from_log(
    log_jsonl: Path,
    *,
    questions_path: Path,
    strategy: str,
    scenario: str,
    temperature: float,
    repeat_idx: int,
    target_qids: Optional[set[str]] = None,
) -> Dict[str, Any]:
    """
    Summarize one run from `per_question_log.jsonl`.

    - If the same `question_id` appears multiple times, keep the newest timestamp.
    - If `target_qids` is provided, summarize only that subset.
    """
    if not log_jsonl.exists():
        return {
            "n": 0,
            "correct": 0,
            "total_calls": 0,
            "total_tokens": 0,
            "total_latency_s": 0.0,
        }

    # qid -> (timestamp, is_correct, calls, tokens, latency)
    latest: Dict[str, Tuple[str, bool, int, int, float]] = {}
    with log_jsonl.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue

            if str(obj.get("questions_path")) != str(questions_path):
                continue
            if str(obj.get("strategy")) != strategy:
                continue
            if str(obj.get("scenario")) != scenario:
                continue
            try:
                if float(obj.get("temperature", -1)) != float(temperature):
                    continue
            except Exception:
                continue
            try:
                if int(obj.get("repeat_idx", -1)) != int(repeat_idx):
                    continue
            except Exception:
                continue

            qid = str(obj.get("question_id") or "")
            if not qid:
                continue
            if target_qids is not None and qid not in target_qids:
                continue

            ts = str(obj.get("timestamp") or "")
            is_correct = bool(obj.get("is_correct"))
            calls = obj.get("calls") or []
            calls_n = len(calls) if isinstance(calls, list) else 0
            usage_sum = obj.get("usage_sum") or {}
            total_tokens = int(usage_sum.get("total_tokens") or 0)
            latency_s = float(obj.get("latency_sum_s") or 0.0)

            prev = latest.get(qid)
            if prev is None or ts >= prev[0]:
                latest[qid] = (ts, is_correct, calls_n, total_tokens, latency_s)

    n = len(latest)
    correct = sum(1 for (_, ok, _, _, _) in latest.values() if ok)
    total_calls = sum(int(calls_n) for (_, _, calls_n, _, _) in latest.values())
    total_tokens = sum(int(toks) for (_, _, _, toks, _) in latest.values())
    total_latency_s = float(sum(float(lat) for (_, _, _, _, lat) in latest.values()))

    return {
        "n": n,
        "correct": correct,
        "total_calls": total_calls,
        "total_tokens": total_tokens,
        "total_latency_s": total_latency_s,
    }


@app.command()
def main(
    strategy: str = typer.Option(
        ...,
        help=f"Strategy name: non-LLM={sorted(NON_LLM_STRATEGIES)}; single-agent={sorted(SINGLE_STRATEGIES)}; multi-agent={sorted(MULTI_STRATEGIES)}",
    ),
    scenario: str = typer.Option("outdoor_dwr_windbreaker", help="Scenario: outdoor_dwr_windbreaker / winter_warm_midlayer"),
    temperature: float = typer.Option(0.6, help="Sampling temperature"),
    repeats: int = typer.Option(2, help="Number of repeated runs"),
    n_questions: int = typer.Option(50, "--n-questions", help="Number of sampled questions per repeat"),
    seed: int = typer.Option(123, help="Question-sampling seed"),
    max_tokens: int = typer.Option(512, help="Maximum output tokens per call"),
    retry_on_none: bool = typer.Option(
        True,
        "--retry-on-none/--no-retry-on-none",
        help="If A/B/C/D cannot be extracted (`pred=None`), retry once with a higher `max_tokens` value and count that retry in calls/tokens/latency.",
    ),
    retry_max_tokens: int = typer.Option(1024, "--retry-max-tokens", help="`max_tokens` used for the retry path (triggered only when `pred=None`)"),
    progress: bool = typer.Option(True, "--progress/--no-progress", help="Show per-question progress and ETA"),
    progress_every: int = typer.Option(1, "--progress-every", help="Print progress every N processed questions"),
    questions_path: Path = typer.Option(Path("data/questions.jsonl"), help="Path to the question pool JSONL"),
    out_dir: Path = typer.Option(Path("outputs"), help="Output directory for results.csv and per_question_log.jsonl"),
    results_name: str = typer.Option("results.csv", "--results-name", help="Output CSV filename, for example `results_main.csv`"),
    log_name: str = typer.Option("per_question_log.jsonl", "--log-name", help="Per-question JSONL log filename, for example `per_question_log_main.jsonl`"),
    skip_existing: bool = typer.Option(
        False,
        "--skip-existing/--no-skip-existing",
        help="Skip a repeat if `results` already contains the same configuration (questions_path/strategy/scenario/t/repeat/n/seed/max_tokens/retry params/model).",
    ),
    log_messages: bool = typer.Option(
        False,
        "--log-messages/--no-log-messages",
        help="Whether to store full prompt/response messages in the per-question log. This increases file size substantially and is usually best left off for main experiments.",
    ),
    abort_on_llm_error: bool = typer.Option(
        True,
        "--abort-on-llm-error/--no-abort-on-llm-error",
        help="Abort the current run immediately if any call returns `[LLM_ERROR]`, preventing zero-token pseudo-results from contaminating the main experiment.",
    ),
    resume: bool = typer.Option(
        False,
        "--resume/--no-resume",
        help="Resume from the per-question log by skipping completed question_ids and rerunning only the remainder.",
    ),
) -> None:
    if strategy not in SINGLE_STRATEGIES and strategy not in MULTI_STRATEGIES and strategy not in NON_LLM_STRATEGIES:
        raise typer.BadParameter(f"Unknown strategy: {strategy}")

    all_q = _read_jsonl(questions_path)
    q_pool = [q for q in all_q if str(q.get("scenario")) == scenario]
    if not q_pool:
        raise typer.BadParameter(f"No questions for scenario={scenario}. Check {questions_path}")

    # Initialize the OpenAI client only for LLM-based strategies so non-LLM
    # baselines do not require an API key.
    llm: Optional[OpenAIClient] = None
    if strategy in SINGLE_STRATEGIES or strategy in MULTI_STRATEGIES:
        llm = OpenAIClient()
        # GPT-5-family models often do not support custom temperatures under the
        # current API behavior, so force temperature=1.0 to keep logs accurate.
        if str(getattr(llm, "model", "")).startswith("gpt-5") and float(temperature) != 1.0:
            typer.echo(f"[note] model={llm.model} does not support temperature={temperature}; forcing temperature=1.0")
            temperature = 1.0
        model_name = str(llm.model)
    else:
        # Non-LLM baselines still reuse the MODEL env var as a config label so
        # they can be compared under the same experiment configuration.
        import os

        model_name = str(os.getenv("MODEL") or "gpt-5-mini")

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
                model=str(model_name),
            )
            if k in existing_keys:
                typer.echo(f"[skip] existing result found for strategy={strategy} scenario={scenario} t={temperature} r={r} n={n} seed={seed} -> {results_csv}")
                continue
        run_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{strategy}_{scenario}_t{temperature}_r{r}_seed{seed}"
        
        # For `--resume`, read already completed question IDs and filter them out.
        completed_qids: set[str] = set()
        if resume:
            completed_qids = _load_completed_qids(
                log_jsonl,
                questions_path=questions_path,
                strategy=strategy,
                scenario=scenario,
                temperature=temperature,
                repeat_idx=r,
                seed=seed,
            )
            if completed_qids:
                typer.echo(f"[resume] found {len(completed_qids)} completed questions for strategy={strategy} scenario={scenario} t={temperature} r={r}")
        
        t_run0 = time.perf_counter()

        if progress:
            pending_count = sum(1 for q in batch if str(q.get("id")) not in completed_qids)
            typer.echo(f"[{run_id}] start: strategy={strategy} scenario={scenario} n_questions={n} pending={pending_count} repeat={r+1}/{repeats}")

        correct = 0
        total_calls = 0
        total_latency = 0.0
        total_tokens = 0

        processed = 0  # Number of questions processed in this invocation.
        for qi, q in enumerate(batch):
            qid = str(q.get("id") or "")
            gold = q.get("answer")
            
            # Skip completed items when resuming.
            if resume and qid in completed_qids:
                continue
            processed += 1

            # Per-call seed: stable within a repeat, but distinct across questions.
            call_seed: Optional[int] = (seed + r * 100_000 + qi) if seed is not None else None

            if strategy in NON_LLM_STRATEGIES:
                out = run_non_llm_strategy(q, strategy=strategy, seed=call_seed)
            elif strategy in SINGLE_STRATEGIES:
                if llm is None:
                    raise RuntimeError("LLM client is not initialized for LLM strategy")
                out = run_single_strategy(llm, q, strategy=strategy, temperature=temperature, max_tokens=max_tokens, seed=call_seed)
            else:
                if llm is None:
                    raise RuntimeError("LLM client is not initialized for LLM strategy")
                out = run_multi_strategy(llm, q, strategy=strategy, temperature=temperature, max_tokens=max_tokens, seed=call_seed)

            pred = out.get("pick")
            retry_info: Optional[Dict[str, Any]] = None
            # Retry only for single-agent strategies; non-LLM and multi-agent
            # paths already have their own fallbacks and usually do not return None.
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
                # Merge the retry records so total calls/tokens/latency stay accurate.
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
                # Main experiments omit full prompt messages by default because the
                # logs become extremely large. Enable `--log-messages` for debugging.
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
                done = processed
                pending_total = n - len(completed_qids) if resume else n
                if (done % progress_every == 0) or (done == pending_total):
                    elapsed = time.perf_counter() - t_run0
                    avg = elapsed / max(1, done)
                    eta = avg * max(0, pending_total - done)
                    acc_so_far = correct / max(1, done)
                    typer.echo(
                        f"[{run_id}] {done}/{pending_total} acc_so_far={acc_so_far:.3f} calls={total_calls} tokens={total_tokens} elapsed_s={elapsed:.1f} eta_s={eta:.1f}"
                    )

        t_run = time.perf_counter() - t_run0
        # `results.csv` should represent the full repeat, even when `--resume` is
        # used. If this run resumed from a partial state, rebuild the aggregate
        # statistics from the log.
        if resume and (completed_qids or processed < n):
            target_qids = {str(q.get("id") or "") for q in batch if str(q.get("id") or "")}
            summary = _summarize_from_log(
                log_jsonl,
                questions_path=questions_path,
                strategy=strategy,
                scenario=scenario,
                temperature=temperature,
                repeat_idx=r,
                target_qids=target_qids,
            )
            actual_n = int(summary["n"])
            correct_total = int(summary["correct"])
            total_calls_total = int(summary["total_calls"])
            total_tokens_total = int(summary["total_tokens"])
            total_latency_total = float(summary["total_latency_s"])
        else:
            actual_n = n
            correct_total = correct
            total_calls_total = total_calls
            total_tokens_total = total_tokens
            total_latency_total = total_latency

        acc = correct_total / max(1, actual_n)
        row = {
            "run_id": run_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "questions_path": str(questions_path),
            "strategy": strategy,
            "scenario": scenario,
            "temperature": temperature,
            "repeat_idx": r,
            "n_questions": actual_n,
            "seed": int(seed),
            "max_tokens": int(max_tokens),
            "retry_on_none": bool(retry_on_none),
            "retry_max_tokens": int(retry_max_tokens),
            "log_messages": bool(log_messages),
            "correct": int(correct_total),
            "accuracy": acc,
            "model": model_name,
            "total_calls": int(total_calls_total),
            "total_tokens": int(total_tokens_total),
            "total_latency_s": round(float(total_latency_total), 6),
            "avg_latency_s": round(float(total_latency_total) / max(1, actual_n), 6),
            "avg_tokens": round(int(total_tokens_total) / max(1, actual_n), 3),
            "avg_calls": round(int(total_calls_total) / max(1, actual_n), 3),
            "wall_time_s": round(t_run, 6),
            "resumed": bool(resume and (len(completed_qids) > 0 or processed < n)),
        }
        _append_csv(results_csv, row)

        typer.echo(
            f"[{run_id}] acc={acc:.3f} correct={int(correct_total)}/{actual_n} calls={int(total_calls_total)} tokens={int(total_tokens_total)} latency_s={float(total_latency_total):.2f} wall_s={t_run:.2f}"
        )


if __name__ == "__main__":
    app()


