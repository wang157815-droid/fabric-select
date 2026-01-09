from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Mapping, Optional

from .llm_client import LLMClient
from .prompts import fashionprompt_template, few_shot_examples, system_prompt_general, user_prompt_mcq

OptionKey = str  # "A"/"B"/"C"/"D"


_RE_TAGGED = re.compile(
    r"(?im)^\s*(?:FINAL|INITIAL|Final|Initial|final|initial|答案|选择|Answer)\s*[:：]\s*[<（(\[]?\s*([ABCD])\s*[>）)\]]?\b"
)
_RE_LINE_ONLY = re.compile(r"(?m)^\s*([ABCD])\s*$")
_RE_STANDALONE = re.compile(r"\b([ABCD])\b")


def extract_pick(text: str) -> Optional[OptionKey]:
    if not text:
        return None

    # 1) JSON
    t = text.strip()
    if t.startswith("{") and t.endswith("}"):
        try:
            obj = json.loads(t)
            for k in ("pick", "answer", "final", "choice"):
                if k in obj and str(obj[k]).strip() in ("A", "B", "C", "D"):
                    return str(obj[k]).strip()
        except Exception:
            pass

    # 2) Tagged line（优先 FINAL/INITIAL 等）
    m = _RE_TAGGED.search(text)
    if m:
        return m.group(1)

    # 3) 单独一行的字母（更可靠）
    line_m = _RE_LINE_ONLY.findall(text)
    if line_m:
        return line_m[-1]

    # 4) 兜底：取最后一个出现的 A/B/C/D（独立词）
    all_m = _RE_STANDALONE.findall(text)
    if all_m:
        return all_m[-1]

    return None


def _call(
    llm: LLMClient,
    messages: List[Dict[str, str]],
    temperature: float,
    max_tokens: int,
    seed: Optional[int],
    call_name: str,
) -> Dict[str, Any]:
    comp = llm.complete(messages=messages, temperature=temperature, max_tokens=max_tokens, seed=seed)
    return {
        "name": call_name,
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


def run_single_strategy(
    llm: LLMClient,
    question: Mapping[str, Any],
    strategy: str,
    temperature: float = 0.6,
    max_tokens: int = 512,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    单智能体策略入口。

    Returns（JSON 可序列化）:
      - pick: "A"/"B"/"C"/"D"（若抽取失败则为 None）
      - calls: 每次 LLM 调用的记录（messages/response/usage/latency）
      - raw_output: 最终一次调用的原始输出
    """

    scenario = str(question["scenario"])
    stem = str(question["stem"])
    options = question["options"]

    calls: List[Dict[str, Any]] = []

    if strategy == "zero_shot":
        messages = [
            {"role": "system", "content": system_prompt_general()},
            {"role": "user", "content": user_prompt_mcq(stem, options, scenario)},
        ]
        calls.append(_call(llm, messages, temperature, max_tokens, seed, call_name="zero_shot"))
        raw = calls[-1]["response_text"]
        return {"pick": extract_pick(raw), "calls": calls, "raw_output": raw}

    if strategy == "few_shot":
        messages = [{"role": "system", "content": system_prompt_general()}]
        messages.extend(few_shot_examples())
        messages.append({"role": "user", "content": user_prompt_mcq(stem, options, scenario)})
        calls.append(_call(llm, messages, temperature, max_tokens, seed, call_name="few_shot"))
        raw = calls[-1]["response_text"]
        return {"pick": extract_pick(raw), "calls": calls, "raw_output": raw}

    if strategy == "cot_few_shot":
        cot_inst = (
            "请先用 2-4 条要点说明你的判断依据（不要输出长篇推理），最后一行只输出：FINAL: X（X 为 A/B/C/D）。"
        )
        messages = [{"role": "system", "content": system_prompt_general()}]
        messages.extend(few_shot_examples())
        messages.append({"role": "user", "content": user_prompt_mcq(stem, options, scenario) + "\n\n" + cot_inst})
        calls.append(_call(llm, messages, temperature, max_tokens, seed, call_name="cot_few_shot"))
        raw = calls[-1]["response_text"]
        return {"pick": extract_pick(raw), "calls": calls, "raw_output": raw}

    if strategy == "self_reflection":
        # Call 1: initial answer
        messages1 = [
            {"role": "system", "content": system_prompt_general()},
            {
                "role": "user",
                "content": user_prompt_mcq(stem, options, scenario)
                + "\n\n请给出初步答案，并附 2-4 条简短依据。最后一行输出：INITIAL: X（X 为 A/B/C/D）。",
            },
        ]
        calls.append(_call(llm, messages1, temperature, max_tokens, seed, call_name="self_reflection_round1"))
        raw1 = calls[-1]["response_text"]
        init_pick = extract_pick(raw1)

        # Call 2: reflect + final
        # IMPORTANT: round2 必须携带原题与选项，否则模型会反复索要信息，导致变慢/产生 None/触发重试。
        # 这里用“同一对话的复盘”格式：user 提供原题 -> assistant 给出初答 -> user 要求复核并只输出 FINAL。
        question_prompt = user_prompt_mcq(stem, options, scenario)
        init_pick_str = init_pick or "（未抽取到）"
        messages2 = [
            {"role": "system", "content": system_prompt_general()},
            {"role": "user", "content": question_prompt},
            {
                "role": "assistant",
                "content": raw1 or f"INITIAL: {init_pick_str}",
            },
            {
                "role": "user",
                "content": (
                    "请复核你刚才的初步答案：先严格检查题目中的硬约束 must（不满足的选项必须淘汰），"
                    "再在剩余选项中按偏好选择最优。"
                    "如果初步答案不对，请纠正。\n\n"
                    "要求：不要输出解释或多余文字；只输出一行：FINAL: X（X 为 A/B/C/D）。"
                ),
            },
        ]
        calls.append(_call(llm, messages2, temperature, max_tokens, seed, call_name="self_reflection_round2"))
        raw2 = calls[-1]["response_text"]
        final_pick = extract_pick(raw2) or init_pick
        return {"pick": final_pick, "calls": calls, "raw_output": raw2}

    if strategy == "fashionprompt":
        sys_fp = (
            "你是资深服装面料/材料决策助手。你会严格按硬约束 must 先淘汰，再按软偏好 prefer 综合权衡。\n"
            "请严格遵守用户给出的结构化输出要求，尤其是第一行必须为 FINAL: X（X 为 A/B/C/D）。"
        )
        messages = [
            {"role": "system", "content": sys_fp},
            {
                "role": "user",
                "content": fashionprompt_template() + "\n\n" + user_prompt_mcq(stem, options, scenario),
            },
        ]
        calls.append(_call(llm, messages, temperature, max_tokens, seed, call_name="fashionprompt"))
        raw = calls[-1]["response_text"]
        return {"pick": extract_pick(raw), "calls": calls, "raw_output": raw}

    raise ValueError(f"Unknown single-agent strategy: {strategy}")


