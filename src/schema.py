from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

ScenarioId = Literal["outdoor_dwr_windbreaker", "winter_warm_midlayer"]


class Compliance(BaseModel):
    pfas_free: bool = Field(..., description="是否 PFAS-free")

    model_config = ConfigDict(extra="allow")


class Care(BaseModel):
    machine_wash: bool = Field(..., description="是否可机洗")

    model_config = ConfigDict(extra="allow")


class FabricCandidate(BaseModel):
    """
    候选面料的通用结构（允许 extra 字段，便于扩展 catalog 字段）。
    """

    id: str

    # outdoor
    water_repellency: Optional[int] = None  # 1..5
    breathability: Optional[int] = None  # 1..5
    abrasion: Optional[int] = None  # 1..5
    handfeel_noise: Optional[int] = None  # 1..5，越高越安静/手感更好
    weight_gsm: Optional[float] = None

    # winter
    loft_or_clo: Optional[float] = None
    wind_blocking: Optional[int] = None  # 1..5
    moisture_management: Optional[int] = None  # 1..5
    bulk_weight: Optional[int] = None  # 1..5，越低越轻薄

    # common
    cost_level: int  # 1..5，越低越便宜
    lead_time_level: int  # 1..5，越低越快
    compliance: Compliance
    care: Optional[Care] = None

    model_config = ConfigDict(extra="allow")


class MCQQuestion(BaseModel):
    id: str
    scenario: ScenarioId
    stem: str
    options: Dict[Literal["A", "B", "C", "D"], Dict[str, Any]]
    answer: Literal["A", "B", "C", "D"]
    key_rationales: List[str]
    option_tags: Optional[Dict[Literal["A", "B", "C", "D"], List[str]]] = None


class AgentDecision(BaseModel):
    """
    多智能体角色输出的统一 JSON 结构（严格与论文/工程约定对齐）。
    """

    pick: Literal["A", "B", "C", "D"]
    confidence: float = Field(..., ge=0.0, le=1.0)
    must_fail: bool
    reasons: List[str]
    risk_notes: List[str]


