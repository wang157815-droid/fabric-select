from __future__ import annotations

import os
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

try:
    # Optional dependency: makes local development convenient, but shouldn't break non-LLM workflows.
    from dotenv import load_dotenv  # type: ignore
except Exception:  # pragma: no cover
    load_dotenv = None  # type: ignore[assignment]

# Retry settings for transient network/service errors.
_RETRY_MAX_ATTEMPTS = 5
_RETRY_BASE_DELAY_S = 2.0
_RETRY_MAX_DELAY_S = 60.0


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
    Shared LLM abstraction layer for future Anthropic / vLLM extensions.
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
    OpenAI API client that reads the `OPENAI_API_KEY` and `MODEL` env vars.

    Prefer the Responses API by default; fall back to Chat Completions when
    needed.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        if load_dotenv is not None:
            load_dotenv()

        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("Missing OPENAI_API_KEY. Please set it in env or .env")

        self.model = model or os.getenv("MODEL") or "gpt-5-mini"
        self.reasoning_effort = os.getenv("REASONING_EFFORT", "low") or None

        # Delay the import so non-LLM scripts can still run without `openai`.
        from openai import OpenAI  # type: ignore

        self._client = OpenAI(api_key=api_key)

    def _is_transient_error(self, e: Exception) -> bool:
        """Return whether the exception looks like a retryable transient error."""
        from openai import APITimeoutError, APIConnectionError, RateLimitError, InternalServerError  # type: ignore
        if isinstance(e, (APITimeoutError, APIConnectionError, RateLimitError, InternalServerError)):
            return True
        s = str(e).lower()
        return any(kw in s for kw in ("timeout", "connection", "rate limit", "internal server", "502", "503", "504"))

    def complete(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.6,
        max_tokens: int = 512,
        seed: Optional[int] = None,
    ) -> LLMCompletion:
        # Outer retry loop for transient timeouts, connection issues, and rate limits.
        last_transient_err: Optional[Exception] = None
        for attempt in range(_RETRY_MAX_ATTEMPTS):
            try:
                return self._complete_inner(messages, temperature, max_tokens, seed)
            except Exception as e:
                if self._is_transient_error(e):
                    last_transient_err = e
                    delay = min(_RETRY_BASE_DELAY_S * (2 ** attempt) + random.uniform(0, 1), _RETRY_MAX_DELAY_S)
                    time.sleep(delay)
                    continue
                raise
        # Retries exhausted: return an explicit LLM_ERROR marker.
        latency = 0.0
        msg = f"[LLM_ERROR] transient error after {_RETRY_MAX_ATTEMPTS} retries: {type(last_transient_err).__name__}: {last_transient_err}"
        return LLMCompletion(text=msg, model=self.model, latency_s=latency, usage=LLMUsage(), raw=None)

    def _complete_inner(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        seed: Optional[int],
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

        # 1) Try the Responses API first.
        try:
            # Some models enforce a minimum `max_output_tokens` (for example >=16).
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

            # Retry automatically when the model rejects optional parameters.
            for _ in range(4):
                try:
                    try:
                        resp = self._client.responses.create(**kwargs)
                    except TypeError as e:
                        # Older OpenAI SDK versions may reject `seed` here.
                        if "seed" in str(e) and "unexpected keyword argument" in str(e):
                            kwargs.pop("seed", None)
                            resp = self._client.responses.create(**kwargs)
                        else:
                            raise
                    break
                except Exception as e:
                    # Drop unsupported params dynamically and retry.
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

            # Some responses expose `output_text` but leave it empty; recover text from `output`.
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
            # 2) Fall back to Chat Completions.
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

        # Try `max_completion_tokens` first; GPT-5-family models often prefer it.
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
                    # If the model rejects temperature, retry without it.
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
    Placeholder for a future Anthropic implementation.
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
    Placeholder for a future vLLM implementation.
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


