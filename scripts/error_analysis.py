#!/usr/bin/env python3
"""
Error-analysis script: sample failed cases from per_question_log.jsonl,
classify them, and write error_analysis.md.
"""
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List

import typer

app = typer.Typer(add_completion=False, help="Sample and classify error cases from per_question_log.")


def classify_error(rec: Dict[str, Any], question: Dict[str, Any] | None) -> str:
    """
    Classify one incorrect record:
    - pred_null: the model did not produce a valid option
    - must_fail_chosen: the model selected an option that violates a hard constraint
    - soft_tradeoff: the model made a soft-preference trade-off error
    - unknown: could not be classified
    """
    pred = rec.get("pred")
    gold = rec.get("gold")
    
    if pred is None or pred not in ("A", "B", "C", "D"):
        return "pred_null"
    
    if question:
        option_tags = question.get("option_tags", {})
        pred_tags = option_tags.get(pred, [])
        if "must_fail" in pred_tags:
            return "must_fail_chosen"
    
    return "soft_tradeoff"


@app.command()
def main(
    log_jsonl: Path = typer.Option(..., "--log", help="Path to per_question_log.jsonl"),
    questions_jsonl: Path = typer.Option(..., "--questions", help="Path to questions_v1_clean.jsonl"),
    out_md: Path = typer.Option(..., "--out", help="Output Markdown file path"),
    sample_size: int = typer.Option(80, "--sample", help="Number of error cases to sample"),
    seed: int = typer.Option(42, "--seed", help="Random seed"),
) -> None:
    random.seed(seed)
    
    # Load questions.
    questions_map: Dict[str, Dict[str, Any]] = {}
    if questions_jsonl.exists():
        with questions_jsonl.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    q = json.loads(line)
                    qid = q.get("id") or ""
                    if qid:
                        questions_map[qid] = q
                except Exception:
                    pass
    typer.echo(f"Loaded {len(questions_map)} questions")
    
    # Load incorrect records.
    errors: List[Dict[str, Any]] = []
    total_records = 0
    with log_jsonl.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                total_records += 1
                if not rec.get("is_correct", True):
                    errors.append(rec)
            except Exception:
                pass
    
    typer.echo(f"Total records: {total_records}, errors: {len(errors)}")
    
    # Aggregate error categories.
    error_types: Counter = Counter()
    errors_by_type: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    errors_by_strategy: Dict[str, Counter] = defaultdict(Counter)
    
    for rec in errors:
        qid = rec.get("question_id", "")
        question = questions_map.get(qid)
        etype = classify_error(rec, question)
        error_types[etype] += 1
        errors_by_type[etype].append(rec)
        strategy = rec.get("strategy", "unknown")
        errors_by_strategy[strategy][etype] += 1
    
    # Sample cases.
    sampled: List[Dict[str, Any]] = []
    # Sample evenly across error types first.
    types_list = list(errors_by_type.keys())
    per_type = max(1, sample_size // len(types_list)) if types_list else 0
    for etype in types_list:
        pool = errors_by_type[etype]
        n = min(per_type, len(pool))
        sampled.extend(random.sample(pool, n))
    
    # Fill the remainder up to `sample_size`.
    remaining = sample_size - len(sampled)
    if remaining > 0:
        all_errors_set = set(id(e) for e in sampled)
        candidates = [e for e in errors if id(e) not in all_errors_set]
        if candidates:
            sampled.extend(random.sample(candidates, min(remaining, len(candidates))))
    
    typer.echo(f"Sampled {len(sampled)} error cases")
    
    # Build the Markdown report.
    lines: List[str] = []
    lines.append("# Error Analysis Report\n")
    lines.append(f"**Total records**: {total_records}  ")
    lines.append(f"**Total errors**: {len(errors)} ({100*len(errors)/total_records:.1f}%)  ")
    lines.append(f"**Sampled for analysis**: {len(sampled)}\n")
    
    lines.append("## Error Type Distribution\n")
    lines.append("| Error Type | Count | Percentage |")
    lines.append("|------------|-------|------------|")
    for etype, cnt in error_types.most_common():
        pct = 100 * cnt / len(errors) if errors else 0
        desc = {
            "pred_null": "No valid option was produced (A/B/C/D)",
            "must_fail_chosen": "A hard-constraint-violating option was chosen",
            "soft_tradeoff": "Soft-preference trade-off failure",
            "unknown": "Unknown type",
        }.get(etype, etype)
        lines.append(f"| {etype} ({desc}) | {cnt} | {pct:.1f}% |")
    lines.append("")
    
    lines.append("## Error Distribution by Strategy\n")
    lines.append("| Strategy | pred_null | must_fail_chosen | soft_tradeoff | Total |")
    lines.append("|----------|-----------|------------------|---------------|-------|")
    strategies = sorted(errors_by_strategy.keys())
    for s in strategies:
        c = errors_by_strategy[s]
        total_s = sum(c.values())
        lines.append(f"| {s} | {c['pred_null']} | {c['must_fail_chosen']} | {c['soft_tradeoff']} | {total_s} |")
    lines.append("")
    
    lines.append("## Sampled Error Cases\n")
    for i, rec in enumerate(sampled[:50], 1):  # Show only the first 50.
        qid = rec.get("question_id", "?")
        strategy = rec.get("strategy", "?")
        scenario = rec.get("scenario", "?")
        gold = rec.get("gold", "?")
        pred = rec.get("pred", "null")
        question = questions_map.get(qid)
        etype = classify_error(rec, question)
        
        lines.append(f"### Case {i}: {qid}")
        lines.append(f"- **Strategy**: {strategy}")
        lines.append(f"- **Scenario**: {scenario}")
        lines.append(f"- **Gold**: {gold}, **Pred**: {pred}")
        lines.append(f"- **Error Type**: {etype}")
        
        if question:
            stem = question.get("stem", "")[:200]
            lines.append(f"- **Question (truncated)**: {stem}...")
            option_tags = question.get("option_tags", {})
            if pred and pred in option_tags:
                lines.append(f"- **Pred option tags**: {option_tags.get(pred, [])}")
        
        # Short raw_output preview.
        raw = rec.get("raw_output") or ""
        if raw:
            preview = raw[:150].replace("\n", " ")
            lines.append(f"- **Raw output preview**: {preview}...")
        lines.append("")
    
    # Write the report.
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines), encoding="utf-8")
    typer.echo(f"Wrote error analysis -> {out_md}")


if __name__ == "__main__":
    app()

