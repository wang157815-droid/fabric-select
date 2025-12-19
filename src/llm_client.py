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

        # 1) 优先尝试 Responses API（更通用）
        try:
            kwargs: Dict[str, Any] = {
                "model": self.model,
                "input": messages,
                "temperature": float(temperature),
                "max_output_tokens": int(max_tokens),
            }
            if seed is not None:
                kwargs["seed"] = int(seed)

            resp = self._client.responses.create(**kwargs)
            latency = time.perf_counter() - t0

            text = getattr(resp, "output_text", None)
            if text is None:
                # 兼容少数返回结构
                text = ""
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
        except Exception:
            # 2) 回退到 Chat Completions（部分账号/模型仍可用）
            pass

        try:
            kwargs2: Dict[str, Any] = {
                "model": self.model,
                "messages": messages,
                "temperature": float(temperature),
                "max_tokens": int(max_tokens),
            }
            if seed is not None:
                kwargs2["seed"] = int(seed)

            resp2 = self._client.chat.completions.create(**kwargs2)
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
            latency3 = time.perf_counter() - t0
            return LLMCompletion(
                text=f"[LLM_ERROR] {type(e).__name__}: {e}",
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


