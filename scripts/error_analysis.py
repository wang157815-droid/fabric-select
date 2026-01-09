#!/usr/bin/env python3
"""
错误分析脚本：从 per_question_log.jsonl 抽样错误案例，分类统计，输出 error_analysis.md
"""
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List

import typer

app = typer.Typer(add_completion=False, help="从 per_question_log 抽样错误案例并分类统计")


def classify_error(rec: Dict[str, Any], question: Dict[str, Any] | None) -> str:
    """
    对一条错误记录进行分类：
    - pred_null: 模型未能输出有效选项
    - must_fail_chosen: 模型选择了违反硬约束的选项
    - soft_tradeoff: 模型在软偏好权衡上失误
    - unknown: 无法分类
    """
    pred = rec.get("pred")
    gold = rec.get("gold")
    
    # 1. 输出为空
    if pred is None or pred not in ("A", "B", "C", "D"):
        return "pred_null"
    
    # 2. 检查是否选了 must_fail 选项
    if question:
        option_tags = question.get("option_tags", {})
        pred_tags = option_tags.get(pred, [])
        if "must_fail" in pred_tags:
            return "must_fail_chosen"
    
    # 3. 其他情况归为软偏好权衡失误
    return "soft_tradeoff"


@app.command()
def main(
    log_jsonl: Path = typer.Option(..., "--log", help="per_question_log.jsonl 路径"),
    questions_jsonl: Path = typer.Option(..., "--questions", help="questions_v1_clean.jsonl 路径"),
    out_md: Path = typer.Option(..., "--out", help="输出 markdown 文件路径"),
    sample_size: int = typer.Option(80, "--sample", help="抽样错误案例数量"),
    seed: int = typer.Option(42, "--seed", help="随机种子"),
) -> None:
    random.seed(seed)
    
    # 加载题目
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
    
    # 加载错误记录
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
    
    # 分类统计
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
    
    # 抽样
    sampled: List[Dict[str, Any]] = []
    # 按类型均匀抽样
    types_list = list(errors_by_type.keys())
    per_type = max(1, sample_size // len(types_list)) if types_list else 0
    for etype in types_list:
        pool = errors_by_type[etype]
        n = min(per_type, len(pool))
        sampled.extend(random.sample(pool, n))
    
    # 补齐到 sample_size
    remaining = sample_size - len(sampled)
    if remaining > 0:
        all_errors_set = set(id(e) for e in sampled)
        candidates = [e for e in errors if id(e) not in all_errors_set]
        if candidates:
            sampled.extend(random.sample(candidates, min(remaining, len(candidates))))
    
    typer.echo(f"Sampled {len(sampled)} error cases")
    
    # 生成 markdown
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
            "pred_null": "模型未输出有效选项 (A/B/C/D)",
            "must_fail_chosen": "选择了违反硬约束的选项",
            "soft_tradeoff": "软偏好权衡失误",
            "unknown": "未知类型",
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
    for i, rec in enumerate(sampled[:50], 1):  # 只展示前50个
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
        
        # 简短的 raw_output 预览
        raw = rec.get("raw_output") or ""
        if raw:
            preview = raw[:150].replace("\n", " ")
            lines.append(f"- **Raw output preview**: {preview}...")
        lines.append("")
    
    # 写入文件
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines), encoding="utf-8")
    typer.echo(f"Wrote error analysis -> {out_md}")


if __name__ == "__main__":
    app()

