from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

AgentId = Literal["aeo", "seo", "competitor"]


# ---- requests ----
class AEORequest(BaseModel):
    brand: str = Field(..., description="Brand/product name to track")
    domain: str | None = Field(None, description="Your website domain, e.g. example.com")
    prompts: list[str] = Field(..., description="Buyer questions to probe answer engines with")


class SEORequest(BaseModel):
    keyword: str = Field(..., description="Target keyword/topic")
    domain: str | None = Field(None, description="Your domain (to locate your ranking)")
    serp_limit: int = 10


class CompetitorRequest(BaseModel):
    competitor_url: str = Field(..., description="Competitor homepage or product URL")
    your_url: str | None = Field(None, description="Your comparable page, for a diff")
    focus: list[str] = Field(default_factory=lambda: ["pricing", "positioning", "messaging", "features"])


class RunRequest(BaseModel):
    agent: AgentId
    input: dict[str, Any]


# ---- responses ----
class AgentResult(BaseModel):
    agent: AgentId
    summary: str
    score: float | None = None  # 0-100 where meaningful
    findings: list[dict[str, Any]] = []
    recommendations: list[str] = []
    raw: dict[str, Any] = {}


class AgentInfo(BaseModel):
    id: AgentId
    name: str
    description: str
    input_schema: dict[str, Any]
