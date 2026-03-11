"""
Rewind a specific run inside a JSONL log.

The script keeps only the first N unique `question_id`s for the target run,
backs up the original file, and leaves malformed JSON lines untouched.
"""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


def _matches_run(obj: dict, *, strategy: str, scenario: str, temperature: float, repeat_idx: int) -> bool:
    if str(obj.get("strategy")) != strategy:
        return False
    if str(obj.get("scenario")) != scenario:
        return False
    try:
        if float(obj.get("temperature", -1)) != float(temperature):
            return False
    except Exception:
        return False
    try:
        if int(obj.get("repeat_idx", -1)) != int(repeat_idx):
            return False
    except Exception:
        return False
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description="Rewind per_question_log JSONL for a specific run.")
    ap.add_argument("--log", type=str, required=True, help="Path to JSONL log file, e.g. outputs/per_question_log_main.jsonl")
    ap.add_argument("--strategy", type=str, required=True)
    ap.add_argument("--scenario", type=str, required=True)
    ap.add_argument("--temperature", type=float, required=True)
    ap.add_argument("--repeat-idx", type=int, required=True)
    ap.add_argument("--keep", type=int, required=True, help="Keep first N unique question_ids for this run")
    ap.add_argument("--dry-run", action="store_true", help="Only print what would happen; do not modify files")
    args = ap.parse_args()

    log_path = Path(args.log)
    if not log_path.exists():
        raise SystemExit(f"log not found: {log_path}")

    keep_n = int(args.keep)
    if keep_n <= 0:
        raise SystemExit("--keep must be > 0")

    # Collect unique question_ids in first-seen order.
    order: list[str] = []
    seen: set[str] = set()
    with log_path.open("r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            try:
                obj = json.loads(s)
            except Exception:
                continue
            if not isinstance(obj, dict):
                continue
            if not _matches_run(
                obj,
                strategy=args.strategy,
                scenario=args.scenario,
                temperature=float(args.temperature),
                repeat_idx=int(args.repeat_idx),
            ):
                continue
            qid = str(obj.get("question_id") or "")
            if not qid:
                continue
            if qid in seen:
                continue
            seen.add(qid)
            order.append(qid)

    total = len(order)
    if total == 0:
        print("No matching run records found; nothing to do.")
        return 0

    if keep_n >= total:
        print(f"Matching run has total_unique_qids={total}. keep={keep_n} >= total; nothing to do.")
        return 0

    keep_qids = set(order[:keep_n])
    drop_n = total - keep_n

    print(
        "Target run:",
        f"strategy={args.strategy}",
        f"scenario={args.scenario}",
        f"temperature={float(args.temperature)}",
        f"repeat_idx={int(args.repeat_idx)}",
        sep=" ",
    )
    print(f"Found total_unique_qids={total}. Will keep={keep_n}, drop={drop_n}.")

    if args.dry_run:
        print("Dry-run: no files modified.")
        return 0

    # Backup before rewriting.
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = log_path.with_suffix(log_path.suffix + f".bak_{ts}")
    shutil.copy2(log_path, backup_path)
    print(f"Backup written: {backup_path}")

    # Rewrite the log and drop later question_ids from the target run.
    tmp_path = log_path.with_suffix(log_path.suffix + ".tmp")
    kept_lines = 0
    dropped_lines = 0
    with log_path.open("r", encoding="utf-8") as fin, tmp_path.open("w", encoding="utf-8") as fout:
        for line in fin:
            s = line.strip()
            if not s:
                fout.write(line)
                kept_lines += 1
                continue
            try:
                obj = json.loads(s)
            except Exception:
                # Keep malformed lines untouched.
                fout.write(line)
                kept_lines += 1
                continue
            if isinstance(obj, dict) and _matches_run(
                obj,
                strategy=args.strategy,
                scenario=args.scenario,
                temperature=float(args.temperature),
                repeat_idx=int(args.repeat_idx),
            ):
                qid = str(obj.get("question_id") or "")
                if qid and (qid not in keep_qids):
                    dropped_lines += 1
                    continue
            fout.write(line)
            kept_lines += 1

    tmp_path.replace(log_path)
    print(f"Rewrote log: kept_lines={kept_lines}, dropped_lines={dropped_lines}")
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())














