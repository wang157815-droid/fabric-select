from __future__ import annotations

import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv


@dataclass
class LLMUsage:
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None


@dataclass
class LLMCompletion:
    text: str
    model: str
    latency_s: float
    usage: LLMUsage
    raw: Any = None


class LLMClient(ABC):
    """
    统一 LLM 抽象层：便于后续扩展到 Anthropic / vLLM 等。
    """

    @abstractmethod
    def complete(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.6,
        max_tokens: int = 512,
        seed: Optional[int] = None,
    ) -> LLMCompletion:
        raise NotImplementedError


class OpenAIClient(LLMClient):
    """
    OpenAI API 客户端（读取 OPENAI_API_KEY, MODEL 环境变量）。

    默认优先走 Responses API；若不可用则回退到 Chat Completions。
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        load_dotenv()

        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("Missing OPENAI_API_KEY. Please set it in env or .env")

        self.model = model or os.getenv("MODEL") or "gpt-5-mini"
        self.reasoning_effort = os.getenv("REASONING_EFFORT", "low") or None

        # 延迟导入，避免未安装 openai 时影响其他脚本（如数据生成/单测）
        from openai import OpenAI  # type: ignore

        self._client = OpenAI(api_key=api_key)

    def complete(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.6,
        max_tokens: int = 512,
        seed: Optional[int] = None,
    ) -> LLMCompletion:
        t0 = time.perf_counter()

        responses_err: Optional[Exception] = None

        def _err_str(e: Exception) -> str:
            try:
                return str(e)
            except Exception:
                return repr(e)

        def _is_unsupported_param(e: Exception, param: str) -> bool:
            s = _err_str(e)
            return (f"Unsupported parameter: '{param}'" in s) or (f"'param': '{param}'" in s)

        def _is_unsupported_value(e: Exception, param: str) -> bool:
            s = _err_str(e)
            return (f"Unsupported value: '{param}'" in s) or (f"'param': '{param}'" in s and "unsupported_value" in s)

        def _is_min_value_error(e: Exception, param: str) -> bool:
            s = _err_str(e)
            return (f"Invalid '{param}': integer below minimum value" in s) or (f"'param': '{param}'" in s and "below minimum" in s)

        # 1) 优先尝试 Responses API（更通用）
        try:
            # 部分模型对 max_output_tokens 有最小值限制（例如 >=16），这里做保底
            safe_max_out = max(16, int(max_tokens))
            kwargs: Dict[str, Any] = {
                "model": self.model,
                "input": messages,
                "temperature": float(temperature),
                "max_output_tokens": safe_max_out,
            }
            if seed is not None:
                kwargs["seed"] = int(seed)
            if self.reasoning_effort is not None:
                kwargs["reasoning"] = {"effort": self.reasoning_effort}

            # 对于“参数不支持”的模型做自动重试：seed/temperature 可能会被拒绝
            for _ in range(4):
                try:
                    try:
                        resp = self._client.responses.create(**kwargs)
                    except TypeError as e:
                        # 部分 openai SDK 版本的 Responses API 可能不接受 seed 参数
                        if "seed" in str(e) and "unexpected keyword argument" in str(e):
                            kwargs.pop("seed", None)
                            resp = self._client.responses.create(**kwargs)
                        else:
                            raise
                    break
                except Exception as e:
                    # 动态剔除不支持的参数并重试
                    if (_is_unsupported_param(e, "temperature") or _is_unsupported_value(e, "temperature")) and "temperature" in kwargs:
                        kwargs.pop("temperature", None)
                        continue
                    if _is_unsupported_param(e, "seed") and "seed" in kwargs:
                        kwargs.pop("seed", None)
                        continue
                    if _is_unsupported_param(e, "reasoning") and "reasoning" in kwargs:
                        kwargs.pop("reasoning", None)
                        continue
                    if _is_min_value_error(e, "max_output_tokens"):
                        kwargs["max_output_tokens"] = max(16, int(kwargs.get("max_output_tokens") or safe_max_out))
                        continue
                    raise
            latency = time.perf_counter() - t0

            # 注意：部分情况下 output_text 字段存在但为空串；此时仍需从 output 里回收 message 文本。
            text = getattr(resp, "output_text", None) or ""
            if not str(text).strip():
                out = getattr(resp, "output", None) or []
                for item in out:
                    content = getattr(item, "content", None) or []
                    for c in content:
                        if getattr(c, "type", None) in ("output_text", "text"):
                            text += getattr(c, "text", "") or ""

            usage_obj = getattr(resp, "usage", None)
            usage = LLMUsage(
                input_tokens=getattr(usage_obj, "input_tokens", None),
                output_tokens=getattr(usage_obj, "output_tokens", None),
                total_tokens=getattr(usage_obj, "total_tokens", None),
            )
            return LLMCompletion(text=text or "", model=self.model, latency_s=latency, usage=usage, raw=resp)
        except Exception as e:
            # 2) 回退到 Chat Completions（部分账号/模型仍可用）
            responses_err = e

        def _chat_call(use_max_completion_tokens: bool, use_seed: bool) -> Any:
            kwargs2: Dict[str, Any] = {
                "model": self.model,
                "messages": messages,
                "temperature": float(temperature),
            }
            if use_max_completion_tokens:
                kwargs2["max_completion_tokens"] = int(max_tokens)
            else:
                kwargs2["max_tokens"] = int(max_tokens)
            if use_seed and seed is not None:
                kwargs2["seed"] = int(seed)
            if self.reasoning_effort is not None:
                kwargs2["reasoning_effort"] = self.reasoning_effort
            return self._client.chat.completions.create(**kwargs2)

        # 先试新参数 max_completion_tokens（gpt-5 系列常需要）
        chat_errs: List[Exception] = []
        for use_mct in (True, False):
            for use_seed in ((seed is not None), False):
                try:
                    resp2 = _chat_call(use_max_completion_tokens=use_mct, use_seed=use_seed)
                    latency2 = time.perf_counter() - t0

                    text2 = ""
                    if resp2.choices and resp2.choices[0].message and resp2.choices[0].message.content:
                        text2 = resp2.choices[0].message.content

                    usage_obj2 = getattr(resp2, "usage", None)
                    usage2 = LLMUsage(
                        input_tokens=getattr(usage_obj2, "prompt_tokens", None),
                        output_tokens=getattr(usage_obj2, "completion_tokens", None),
                        total_tokens=getattr(usage_obj2, "total_tokens", None),
                    )
                    return LLMCompletion(text=text2, model=self.model, latency_s=latency2, usage=usage2, raw=resp2)
                except Exception as e:
                    # 若模型不支持 temperature，则去掉温度再试一次（保持 max_tokens/max_completion_tokens 不变）
                    if _is_unsupported_param(e, "temperature") or _is_unsupported_value(e, "temperature"):
                        try:
                            def _chat_call_no_temp() -> Any:
                                kwargs3: Dict[str, Any] = {"model": self.model, "messages": messages}
                                if use_mct:
                                    kwargs3["max_completion_tokens"] = int(max_tokens)
                                else:
                                    kwargs3["max_tokens"] = int(max_tokens)
                                if use_seed and seed is not None:
                                    kwargs3["seed"] = int(seed)
                                if self.reasoning_effort is not None:
                                    kwargs3["reasoning_effort"] = self.reasoning_effort
                                return self._client.chat.completions.create(**kwargs3)

                            resp3 = _chat_call_no_temp()
                            latency3 = time.perf_counter() - t0

                            text3 = ""
                            if resp3.choices and resp3.choices[0].message and resp3.choices[0].message.content:
                                text3 = resp3.choices[0].message.content

                            usage_obj3 = getattr(resp3, "usage", None)
                            usage3 = LLMUsage(
                                input_tokens=getattr(usage_obj3, "prompt_tokens", None),
                                output_tokens=getattr(usage_obj3, "completion_tokens", None),
                                total_tokens=getattr(usage_obj3, "total_tokens", None),
                            )
                            return LLMCompletion(text=text3, model=self.model, latency_s=latency3, usage=usage3, raw=resp3)
                        except Exception as e2:
                            chat_errs.append(e2)
                            continue

                    chat_errs.append(e)

        latency3 = time.perf_counter() - t0
        parts: List[str] = []
        if responses_err is not None:
            parts.append(f"responses: {type(responses_err).__name__}: {responses_err}")
        if chat_errs:
            last = chat_errs[-1]
            parts.append(f"chat: {type(last).__name__}: {last}")
        msg = "; ".join(parts) if parts else "Unknown error"
        return LLMCompletion(
            text=f"[LLM_ERROR] {msg}",
            model=self.model,
            latency_s=latency3,
            usage=LLMUsage(),
            raw=None,
        )


class AnthropicClient(LLMClient):
    """
    占位：后续可实现（接口保持与 LLMClient 兼容）。
    """

    def __init__(self, *args: Any, **kwargs: Any):
        raise NotImplementedError("AnthropicClient is a placeholder for future extension.")

    def complete(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.6,
        max_tokens: int = 512,
        seed: Optional[int] = None,
    ) -> LLMCompletion:
        raise NotImplementedError


class VLLMClient(LLMClient):
    """
    占位：后续可实现（接口保持与 LLMClient 兼容）。
    """

    def __init__(self, *args: Any, **kwargs: Any):
        raise NotImplementedError("VLLMClient is a placeholder for future extension.")

    def complete(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.6,
        max_tokens: int = 512,
        seed: Optional[int] = None,
    ) -> LLMCompletion:
        raise NotImplementedError


