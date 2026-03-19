from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

ScenarioId = Literal["outdoor_dwr_windbreaker", "winter_warm_midlayer"]


class Compliance(BaseModel):
    pfas_free: bool = Field(..., description="Whether the material is PFAS-free")

    model_config = ConfigDict(extra="allow")


class Care(BaseModel):
    machine_wash: bool = Field(..., description="Whether the material is machine washable")

    model_config = ConfigDict(extra="allow")


class FabricCandidate(BaseModel):
    """
    Shared structure for fabric candidates.

    Extra fields are allowed so catalog-specific attributes can be extended
    without changing the base schema.
    """

    id: str

    # outdoor
    water_repellency: Optional[int] = None  # 1..5
    breathability: Optional[int] = None  # 1..5
    abrasion: Optional[int] = None  # 1..5
    handfeel_noise: Optional[int] = None  # 1..5, higher means quieter and better handfeel
    weight_gsm: Optional[float] = None

    # winter
    loft_or_clo: Optional[float] = None
    wind_blocking: Optional[int] = None  # 1..5
    moisture_management: Optional[int] = None  # 1..5
    bulk_weight: Optional[int] = None  # 1..5, lower means lighter and less bulky

    # common
    cost_level: int  # 1..5, lower means cheaper
    lead_time_level: int  # 1..5, lower means faster
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
    Unified JSON structure for multi-agent role outputs.
    """

    pick: Literal["A", "B", "C", "D"]
    confidence: float = Field(..., ge=0.0, le=1.0)
    must_fail: bool
    reasons: List[str]
    risk_notes: List[str]


