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
    ("textile", "面料工程师（Textile Engineer）：关注拒水/透气/耐磨/手感等性能与材料可行性。"),
    ("technical", "工艺/版型技术（Technical/Process）：关注工艺可实现性、耐用性、洗护与穿着体验风险。"),
    ("sourcing", "采购供应链（Sourcing/Supply Chain）：关注成本、交期、供货稳定性与可替代性。"),
    ("product", "产品经理/买手（Product/Merchandiser）：关注用户体验、定位、卖点与整体权衡。"),
    ("compliance", "合规与可持续（Compliance/Sustainability）：关注 PFAS-free 等合规与可持续风险。"),
]

WEIGHTS_OUTDOOR = {"textile": 0.40, "compliance": 0.20, "technical": 0.15, "product": 0.15, "sourcing": 0.10}
WEIGHTS_WINTER = {"textile": 0.35, "technical": 0.20, "product": 0.20, "sourcing": 0.15, "compliance": 0.10}

_RE_PICK = re.compile(r"\b([ABCD])\b")
_RE_RANKING = re.compile(r"ranking\s*:\s*([ABCD])\s*>\s*([ABCD])\s*>\s*([ABCD])\s*>\s*([ABCD])", re.I)

# 多角色并发（可选加速）：
# - 默认 1：保持“串行调用”的基线行为（更稳定、限流风险更低、便于复现实验）
# - 如需加速（仅减少 wall time，不改变算法/结果理论上应一致），可设置环境变量：
#     MULTI_ROLE_PARALLELISM=3  （常用）
#     MULTI_ROLE_PARALLELISM=5  （全并发：更快但更容易触发限流/网络波动）
def _multi_role_parallelism() -> int:
    try:
        v = int(os.getenv("MULTI_ROLE_PARALLELISM", "1"))
    except Exception:
        v = 1
    # 1~8 之间
    return max(1, min(8, v))


def _safe_json(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    t = text.strip()
    # 直接 JSON
    if t.startswith("{") and t.endswith("}"):
        try:
            return json.loads(t)
        except Exception:
            pass
    # 抽取首个 {...}
    try:
        i = t.index("{")
        j = t.rindex("}")
        return json.loads(t[i : j + 1])
    except Exception:
        return None


def _parse_agent_decision(text: str) -> Dict[str, Any]:
    t0 = (text or "").strip()
    if t0.startswith("[LLM_ERROR]"):
        # 明确标记调用失败：不要默认 pick='A'，否则会污染投票/加权的统计结果
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
        "你是资深服装面料/材料决策专家。你会严格按硬约束 must 先淘汰，再按软偏好 prefer 综合权衡。\n\n"
        + role_desc
        + "\n\n你必须只输出一个 JSON 对象，且不能包含任何额外文本（包括代码块围栏）。键必须包含：pick, confidence, must_fail, reasons, risk_notes。\n"
        + "其中：\n"
        + "- pick: A/B/C/D\n"
        + "- confidence: 0.0~1.0\n"
        + "- must_fail: 你所选 pick 是否违反 must（若不确定，宁可标记 true 并在 reasons 说明）\n"
        + "- reasons: 3-6 条\n"
        + "- risk_notes: 1-4 条\n"
        + "额外要求：reasons 的第一条请给出全排序，格式严格为：ranking: A>B>C>D（用于 Borda 聚合）。"
    )


def _agent_user_prompt(question: Mapping[str, Any]) -> str:
    scenario = str(question["scenario"])
    stem = str(question["stem"])
    options = question["options"]
    return stem + "\n\n候选如下：\n" + format_options(options, scenario) + "\n\n请严格只输出 JSON。"


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
        # 全部 must_fail：退化为计数（不忽略）
        for d in decisions.values():
            pick = d.get("pick")
            if pick not in ("A", "B", "C", "D"):
                continue
            counts[pick] += 1.0
            conf_sum[pick] += float(d.get("confidence", 0.5))

    if sum(counts.values()) == 0:
        # 仍然没有有效 pick（例如全是 llm_error）：返回 None
        return None, {k: 0.0 for k in ("A", "B", "C", "D")}

    best = max(
        counts.keys(),
        key=lambda k: (
            counts[k],
            conf_sum[k],
            -ord(k),  # tie-break：字母越靠前越优
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
        # 若全部被 must_fail 过滤，退化为不忽略 must_fail
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
            # fallback：只给 pick 最高分
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
    多智能体策略入口。
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

        # 并发调用：先收集结果，再按 ROLES 顺序写入（保证日志稳定）
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
                    # 极端情况下（线程/客户端异常），降级为一次 LLM_ERROR 记录，避免整题崩掉
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
        # Round 1：只召集权重最高的 3 个角色
        sorted_roles = sorted(role_weights.items(), key=lambda kv: kv[1], reverse=True)
        r1_roles = [kv[0] for kv in sorted_roles[:3]]
        r2_roles = [r for r, _ in ROLES if r not in r1_roles]

        call_roles(r1_roles, round_name="r1")
        pick1, dist1 = _aggregate_weighted(decisions, role_weights=role_weights)
        top1, gap = _top1_gap(dist1)

        # early-stop
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

        # Round 2：补齐剩余角色
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


