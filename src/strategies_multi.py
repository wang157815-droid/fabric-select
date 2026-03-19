from __future__ import annotations

import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Mapping, Optional, Tuple

from .llm_client import LLMClient
from .prompts import format_options

OptionKey = str  # "A"/"B"/"C"/"D"


ROLES: List[Tuple[str, str]] = [
    ("textile", "Textile Engineer: focuses on water repellency, breathability, abrasion, handfeel, and material feasibility."),
    ("technical", "Technical/Process Specialist: focuses on manufacturability, durability, care requirements, and wear comfort risks."),
    ("sourcing", "Sourcing/Supply Chain: focuses on cost, lead time, supply stability, and substitutability."),
    ("product", "Product/Merchandising: focuses on user experience, positioning, selling points, and overall trade-offs."),
    ("compliance", "Compliance/Sustainability: focuses on PFAS-free requirements and other compliance or sustainability risks."),
]

WEIGHTS_OUTDOOR = {"textile": 0.40, "compliance": 0.20, "technical": 0.15, "product": 0.15, "sourcing": 0.10}
WEIGHTS_WINTER = {"textile": 0.35, "technical": 0.20, "product": 0.20, "sourcing": 0.15, "compliance": 0.10}

_RE_PICK = re.compile(r"\b([ABCD])\b")
_RE_RANKING = re.compile(r"ranking\s*:\s*([ABCD])\s*>\s*([ABCD])\s*>\s*([ABCD])\s*>\s*([ABCD])", re.I)

# Optional multi-role parallelism:
# - Default `1`: keeps the serial baseline behavior for stability, lower rate-limit
#   risk, and easier reproducibility.
# - To reduce wall time without changing the algorithm, set for example:
#     MULTI_ROLE_PARALLELISM=3
#     MULTI_ROLE_PARALLELISM=5
def _multi_role_parallelism() -> int:
    try:
        v = int(os.getenv("MULTI_ROLE_PARALLELISM", "1"))
    except Exception:
        v = 1
    # Keep it in a conservative range.
    return max(1, min(8, v))


def _safe_json(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    t = text.strip()
    # Direct JSON
    if t.startswith("{") and t.endswith("}"):
        try:
            return json.loads(t)
        except Exception:
            pass
    # Extract the first {...} block
    try:
        i = t.index("{")
        j = t.rindex("}")
        return json.loads(t[i : j + 1])
    except Exception:
        return None


def _parse_agent_decision(text: str) -> Dict[str, Any]:
    t0 = (text or "").strip()
    if t0.startswith("[LLM_ERROR]"):
        # Mark failed calls explicitly so we do not silently bias aggregation.
        return {
            "pick": None,
            "confidence": 0.0,
            "must_fail": True,
            "reasons": ["llm_error"],
            "risk_notes": [t0[:200]],
            "llm_error": True,
        }

    obj = _safe_json(text) or {}

    pick = str(obj.get("pick", "")).strip()
    if pick not in ("A", "B", "C", "D"):
        m = _RE_PICK.findall(text)
        pick = m[-1] if m else None

    conf = obj.get("confidence", 0.5)
    try:
        conf = float(conf)
    except Exception:
        conf = 0.5
    conf = max(0.0, min(1.0, conf))

    must_fail = bool(obj.get("must_fail", False))
    reasons = obj.get("reasons") or []
    risk_notes = obj.get("risk_notes") or []

    if not isinstance(reasons, list):
        reasons = [str(reasons)]
    if not isinstance(risk_notes, list):
        risk_notes = [str(risk_notes)]

    return {
        "pick": pick,
        "confidence": conf,
        "must_fail": must_fail,
        "reasons": [str(x) for x in reasons],
        "risk_notes": [str(x) for x in risk_notes],
        "llm_error": False,
    }


def _agent_system_prompt(role_desc: str) -> str:
    return (
        "You are an experienced apparel fabric/material decision expert. "
        "Strictly eliminate options that violate hard constraints (`must`) "
        "before trading off soft preferences (`prefer`).\n\n"
        + role_desc
        + "\n\nYou must output exactly one JSON object and no extra text "
        + "(including no code fences). Required keys: pick, confidence, "
        + "must_fail, reasons, risk_notes.\n"
        + "Definitions:\n"
        + "- pick: A/B/C/D\n"
        + "- confidence: 0.0-1.0\n"
        + "- must_fail: whether your selected pick violates a `must` constraint "
        + "(if unsure, prefer `true` and explain in `reasons`)\n"
        + "- reasons: 3-6 items\n"
        + "- risk_notes: 1-4 items\n"
        + "Extra requirement: the first item in `reasons` must provide a full "
        + "ranking in this exact format: ranking: A>B>C>D (used for Borda aggregation)."
    )


def _agent_user_prompt(question: Mapping[str, Any]) -> str:
    scenario = str(question["scenario"])
    stem = str(question["stem"])
    options = question["options"]
    return stem + "\n\nCandidates:\n" + format_options(options, scenario) + "\n\nOutput JSON only."


def _call_agent(
    llm: LLMClient,
    role_name: str,
    role_desc: str,
    question: Mapping[str, Any],
    temperature: float,
    max_tokens: int,
    seed: Optional[int],
    round_name: str,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    messages = [
        {"role": "system", "content": _agent_system_prompt(role_desc)},
        {"role": "user", "content": _agent_user_prompt(question)},
    ]
    comp = llm.complete(messages=messages, temperature=temperature, max_tokens=max_tokens, seed=seed)
    call_record = {
        "name": f"{round_name}:{role_name}",
        "role": role_name,
        "messages": messages,
        "response_text": comp.text,
        "model": comp.model,
        "latency_s": comp.latency_s,
        "usage": {
            "input_tokens": comp.usage.input_tokens,
            "output_tokens": comp.usage.output_tokens,
            "total_tokens": comp.usage.total_tokens,
        },
    }
    decision = _parse_agent_decision(comp.text)
    return decision, call_record


def _aggregate_voting(decisions: Mapping[str, Dict[str, Any]]) -> Tuple[Optional[OptionKey], Dict[str, float]]:
    counts: Dict[str, float] = {k: 0.0 for k in ("A", "B", "C", "D")}
    conf_sum: Dict[str, float] = {k: 0.0 for k in ("A", "B", "C", "D")}
    for d in decisions.values():
        if d.get("must_fail"):
            continue
        pick = d.get("pick")
        if pick not in ("A", "B", "C", "D"):
            continue
        counts[pick] += 1.0
        conf_sum[pick] += float(d.get("confidence", 0.5))

    if sum(counts.values()) == 0:
        # If all votes are must-fail, fall back to raw counting.
        for d in decisions.values():
            pick = d.get("pick")
            if pick not in ("A", "B", "C", "D"):
                continue
            counts[pick] += 1.0
            conf_sum[pick] += float(d.get("confidence", 0.5))

    if sum(counts.values()) == 0:
        # Still no valid pick (for example all are llm_error): return None.
        return None, {k: 0.0 for k in ("A", "B", "C", "D")}

    best = max(
        counts.keys(),
        key=lambda k: (
            counts[k],
            conf_sum[k],
            -ord(k),  # tie-break: earlier letter wins
        ),
    )
    total = sum(counts.values()) or 1.0
    dist = {k: v / total for k, v in counts.items()}
    return best, dist


def _aggregate_weighted(decisions: Mapping[str, Dict[str, Any]], role_weights: Mapping[str, float]) -> Tuple[Optional[OptionKey], Dict[str, float]]:
    scores: Dict[str, float] = {k: 0.0 for k in ("A", "B", "C", "D")}
    for role, d in decisions.items():
        if d.get("must_fail"):
            continue
        pick = d.get("pick")
        if pick not in ("A", "B", "C", "D"):
            continue
        w = float(role_weights.get(role, 1.0))
        scores[pick] += w * float(d.get("confidence", 0.5))

    if sum(scores.values()) == 0:
        # If everything was filtered out, fall back to ignoring `must_fail`.
        for role, d in decisions.items():
            pick = d.get("pick")
            if pick not in ("A", "B", "C", "D"):
                continue
            w = float(role_weights.get(role, 1.0))
            scores[pick] += w * float(d.get("confidence", 0.5))

    if sum(scores.values()) == 0:
        return None, {k: 0.0 for k in ("A", "B", "C", "D")}

    best = max(scores.keys(), key=lambda k: (scores[k], -ord(k)))
    total = sum(scores.values()) or 1.0
    dist = {k: v / total for k, v in scores.items()}
    return best, dist


def _aggregate_borda(decisions: Mapping[str, Dict[str, Any]], role_weights: Mapping[str, float]) -> Tuple[Optional[OptionKey], Dict[str, float]]:
    # Borda points: 3,2,1,0
    points = {0: 3.0, 1: 2.0, 2: 1.0, 3: 0.0}
    scores: Dict[str, float] = {k: 0.0 for k in ("A", "B", "C", "D")}

    for role, d in decisions.items():
        w = float(role_weights.get(role, 1.0))
        ranking = None
        for r in d.get("reasons", [])[:1]:
            m = _RE_RANKING.search(str(r))
            if m:
                ranking = list(m.groups())
                break
        if ranking and len(set(ranking)) == 4:
            for i, opt in enumerate(ranking):
                scores[opt] += w * points[i]
        else:
            # Fallback: award only the selected pick.
            pick = d.get("pick")
            if pick in ("A", "B", "C", "D"):
                scores[pick] += w * points[0]

    if sum(scores.values()) == 0:
        return None, {k: 0.0 for k in ("A", "B", "C", "D")}

    best = max(scores.keys(), key=lambda k: (scores[k], -ord(k)))
    total = sum(scores.values()) or 1.0
    dist = {k: v / total for k, v in scores.items()}
    return best, dist


def _top1_gap(dist: Mapping[str, float]) -> Tuple[float, float]:
    items = sorted(dist.items(), key=lambda kv: kv[1], reverse=True)
    top1 = items[0][1]
    top2 = items[1][1] if len(items) > 1 else 0.0
    return top1, (top1 - top2)


def run_multi_strategy(
    llm: LLMClient,
    question: Mapping[str, Any],
    strategy: str,
    temperature: float = 0.6,
    max_tokens: int = 512,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Entry point for multi-agent strategies.
    """

    scenario = str(question["scenario"])
    role_weights = WEIGHTS_OUTDOOR if scenario == "outdoor_dwr_windbreaker" else WEIGHTS_WINTER

    calls: List[Dict[str, Any]] = []
    decisions: Dict[str, Dict[str, Any]] = {}

    def call_roles(role_names: List[str], round_name: str) -> None:
        selected = [(rn, desc) for rn, desc in ROLES if rn in set(role_names)]
        if not selected:
            return

        par = _multi_role_parallelism()
        if par <= 1 or len(selected) <= 1:
            for rn, desc in selected:
                d, call_rec = _call_agent(llm, rn, desc, question, temperature, max_tokens, seed, round_name=round_name)
                decisions[rn] = d
                calls.append(call_rec)
            return

        # Collect concurrent results first, then append them in stable role order.
        tmp: Dict[str, Tuple[Dict[str, Any], Dict[str, Any]]] = {}
        with ThreadPoolExecutor(max_workers=min(par, len(selected))) as ex:
            futs = {
                ex.submit(_call_agent, llm, rn, desc, question, temperature, max_tokens, seed, round_name): rn
                for rn, desc in selected
            }
            for fut in as_completed(list(futs.keys())):
                rn = futs[fut]
                try:
                    d, call_rec = fut.result()
                except Exception as e:
                    # Extreme fallback: convert thread/client exceptions into a
                    # synthetic LLM_ERROR record so the whole question does not crash.
                    msg = f"[LLM_ERROR] exception in multi-role call: {type(e).__name__}: {e}"
                    d = {
                        "pick": None,
                        "confidence": 0.0,
                        "must_fail": True,
                        "reasons": ["llm_error"],
                        "risk_notes": [str(e)[:200]],
                        "llm_error": True,
                    }
                    call_rec = {
                        "name": f"{round_name}:{rn}",
                        "role": rn,
                        "messages": [],
                        "response_text": msg,
                        "model": "",
                        "latency_s": 0.0,
                        "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
                    }
                tmp[rn] = (d, call_rec)

        for rn, _desc in ROLES:
            if rn not in tmp:
                continue
            d, call_rec = tmp[rn]
            decisions[rn] = d
            calls.append(call_rec)

    if strategy in ("voting", "weighted_voting", "borda"):
        all_roles = [r for r, _ in ROLES]
        call_roles(all_roles, round_name="r1")
        if strategy == "voting":
            pick, dist = _aggregate_voting(decisions)
        elif strategy == "weighted_voting":
            pick, dist = _aggregate_weighted(decisions, role_weights={r: 1.0 for r in all_roles})
        else:
            pick, dist = _aggregate_borda(decisions, role_weights={r: 1.0 for r in all_roles})
        top1, gap = _top1_gap(dist)
        return {
            "pick": pick,
            "calls": calls,
            "agent_decisions": decisions,
            "aggregation": {"method": strategy, "dist": dist, "top1": top1, "top1_gap": gap},
        }

    if strategy == "garmentagents_fixed":
        all_roles = [r for r, _ in ROLES]
        call_roles(all_roles, round_name="r1")
        pick, dist = _aggregate_weighted(decisions, role_weights=role_weights)
        top1, gap = _top1_gap(dist)
        return {
            "pick": pick,
            "calls": calls,
            "agent_decisions": decisions,
            "aggregation": {"method": "weighted_voting", "role_weights": role_weights, "dist": dist, "top1": top1, "top1_gap": gap},
        }

    if strategy == "garmentagents_adaptive":
        # Call the top-3 weighted roles first.
        sorted_roles = sorted(role_weights.items(), key=lambda kv: kv[1], reverse=True)
        r1_roles = [kv[0] for kv in sorted_roles[:3]]
        r2_roles = [r for r, _ in ROLES if r not in r1_roles]

        call_roles(r1_roles, round_name="r1")
        pick1, dist1 = _aggregate_weighted(decisions, role_weights=role_weights)
        top1, gap = _top1_gap(dist1)

        # Stop early once the consensus is sufficiently stable.
        if top1 >= 0.70 or gap >= 0.25:
            return {
                "pick": pick1,
                "calls": calls,
                "agent_decisions": decisions,
                "aggregation": {
                    "method": "adaptive_weighted_voting_early_stop",
                    "rounds": 1,
                    "role_weights": role_weights,
                    "dist": dist1,
                    "top1": top1,
                    "top1_gap": gap,
                },
            }

        # Otherwise query the remaining roles.
        call_roles(r2_roles, round_name="r2")
        pick2, dist2 = _aggregate_weighted(decisions, role_weights=role_weights)
        top1b, gapb = _top1_gap(dist2)
        return {
            "pick": pick2,
            "calls": calls,
            "agent_decisions": decisions,
            "aggregation": {
                "method": "adaptive_weighted_voting_early_stop",
                "rounds": 2,
                "role_weights": role_weights,
                "dist": dist2,
                "top1": top1b,
                "top1_gap": gapb,
            },
        }

    raise ValueError(f"Unknown multi-agent strategy: {strategy}")


