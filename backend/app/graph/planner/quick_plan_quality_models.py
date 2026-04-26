from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


QuickPlanQualityStatus = Literal["pass", "repairable", "fail"]
QuickPlanQualityDimension = Literal[
    "geography",
    "pacing",
    "local_specificity",
    "user_fit",
    "logistics_realism",
    "fact_safety",
]
QuickPlanQualityIssueSeverity = Literal["low", "medium", "high"]


class QuickPlanQualityIssue(BaseModel):
    dimension: QuickPlanQualityDimension
    severity: QuickPlanQualityIssueSeverity = "medium"
    issue: str = Field(..., min_length=1, max_length=260)
    repair_instruction: str | None = Field(default=None, max_length=260)


class QuickPlanQualityScorecard(BaseModel):
    geography: int = Field(default=0, ge=0, le=10)
    pacing: int = Field(default=0, ge=0, le=10)
    local_specificity: int = Field(default=0, ge=0, le=10)
    user_fit: int = Field(default=0, ge=0, le=10)
    logistics_realism: int = Field(default=0, ge=0, le=10)
    fact_safety: int = Field(default=0, ge=0, le=10)

    def score_for(self, dimension: QuickPlanQualityDimension) -> int:
        return int(getattr(self, dimension))


class QuickPlanSpecialistReviewSummary(BaseModel):
    specialist: str = Field(..., min_length=1, max_length=80)
    status: QuickPlanQualityStatus | None = None
    show_to_user: bool | None = None
    review_notes: list[str] = Field(default_factory=list, max_length=6)
    issue_count: int = Field(default=0, ge=0, le=16)


class QuickPlanQualityReviewResult(BaseModel):
    status: QuickPlanQualityStatus
    show_to_user: bool = False
    scorecard: QuickPlanQualityScorecard = Field(
        default_factory=QuickPlanQualityScorecard
    )
    issues: list[QuickPlanQualityIssue] = Field(default_factory=list, max_length=16)
    review_notes: list[str] = Field(default_factory=list, max_length=12)
    repair_instructions: list[str] = Field(default_factory=list, max_length=12)
    assistant_summary: str | None = Field(default=None, max_length=420)
    specialist_results: list[QuickPlanSpecialistReviewSummary] = Field(
        default_factory=list,
        max_length=8,
    )
