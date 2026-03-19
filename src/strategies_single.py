from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Mapping, Optional

from .llm_client import LLMClient
from .prompts import fashionprompt_template, few_shot_examples, system_prompt_general, user_prompt_mcq

OptionKey = str  # "A"/"B"/"C"/"D"


_RE_TAGGED = re.compile(
    r"(?im)^\s*(?:FINAL|INITIAL|Final|Initial|final|initial|Answer|Choice)\s*[:：]\s*[<(\[]?\s*([ABCD])\s*[>)\]]?\b"
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

    # 2) Tagged line (prefer FINAL/INITIAL when present)
    m = _RE_TAGGED.search(text)
    if m:
        return m.group(1)

    # 3) A standalone letter on its own line
    line_m = _RE_LINE_ONLY.findall(text)
    if line_m:
        return line_m[-1]

    # 4) Fallback: take the last standalone A/B/C/D token
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
    Entry point for single-agent strategies.

    Returns (JSON-serializable):
      - pick: "A"/"B"/"C"/"D" (or None if extraction fails)
      - calls: records for each LLM call (messages/response/usage/latency)
      - raw_output: raw output from the final call
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
            "First give 2-4 short bullet points for your evidence (do not provide long chain-of-thought). "
            "On the final line output only: FINAL: X (where X is A/B/C/D)."
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
                + "\n\nGive an initial answer with 2-4 short reasons. On the final line output: INITIAL: X (where X is A/B/C/D).",
            },
        ]
        calls.append(_call(llm, messages1, temperature, max_tokens, seed, call_name="self_reflection_round1"))
        raw1 = calls[-1]["response_text"]
        init_pick = extract_pick(raw1)

        # Call 2: reflect + final
        # IMPORTANT: round 2 must include the original question and options;
        # otherwise the model may ask for missing context, become slower, or
        # return None and trigger retries.
        question_prompt = user_prompt_mcq(stem, options, scenario)
        init_pick_str = init_pick or "(not extracted)"
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
                    "Review your initial answer carefully. First enforce the hard constraints (`must`) "
                    "and eliminate any violating options. Then choose the best remaining option using the "
                    "soft preferences. If your initial answer was wrong, correct it.\n\n"
                    "Requirement: do not output explanations or extra text; output exactly one line: "
                    "FINAL: X (where X is A/B/C/D)."
                ),
            },
        ]
        calls.append(_call(llm, messages2, temperature, max_tokens, seed, call_name="self_reflection_round2"))
        raw2 = calls[-1]["response_text"]
        final_pick = extract_pick(raw2) or init_pick
        return {"pick": final_pick, "calls": calls, "raw_output": raw2}

    if strategy == "fashionprompt":
        sys_fp = (
            "You are an experienced apparel fabric/material decision assistant. "
            "Strictly eliminate options that violate hard constraints (`must`) "
            "before trading off soft preferences (`prefer`).\n"
            "Follow the required output format exactly, especially the first line: "
            "FINAL: X (where X is A/B/C/D)."
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


