from typing import Literal

from pydantic import BaseModel, Field


EvidenceStatus = Literal["verified", "claimed", "none"]
RoleFamily = Literal["all", "application", "algorithm", "product"]


class EvidenceItem(BaseModel):
    skill: str
    status: EvidenceStatus = "none"
    title: str = ""
    url: str = ""
    note: str = ""


class PriorityRequest(BaseModel):
    evidence: list[EvidenceItem] = Field(default_factory=list)
    role_family: RoleFamily = "all"


class SprintRequest(BaseModel):
    skill: str
    daily_minutes: int = Field(default=90, ge=30, le=360)


class CheckIn(BaseModel):
    day: int = Field(ge=1, le=7)
    completed: bool = False
    actual_minutes: int = Field(default=0, ge=0, le=1440)
    artifact_url: str = ""
    note: str = ""
    blocker: str = ""
    next_step: str = ""


class ReportRequest(BaseModel):
    estimated_minutes: int = Field(ge=0)
    checkins: list[CheckIn] = Field(default_factory=list)
