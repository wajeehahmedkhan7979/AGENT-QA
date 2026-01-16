from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, HttpUrl

from db import JobScope, JobStatus


class PreflightResult(BaseModel):
    allowed: bool
    robots: str | None = None


class JobCreateRequest(BaseModel):
    targetUrl: HttpUrl = Field(alias="targetUrl")
    scope: JobScope
    testProfile: str = Field(alias="testProfile")
    ownerId: str = Field(alias="ownerId")

    class Config:
        populate_by_name = True


class ConsentRecord(BaseModel):
    ownerId: str
    consentTimestamp: datetime
    note: Optional[str] = None


class JobResponse(BaseModel):
    jobId: str
    status: JobStatus
    preflight: Optional[PreflightResult] = None
    createdAt: datetime
    consent: list[ConsentRecord] = []
    extra: dict[str, Any] = {}


class ArtifactItem(BaseModel):
    name: str
    type: str
    path: str

