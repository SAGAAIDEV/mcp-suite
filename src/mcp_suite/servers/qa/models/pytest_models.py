"""Models for pytest results."""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class PytestSummary(BaseModel):
    """Summary of pytest results."""

    model_config = ConfigDict(extra="allow")

    total: int = 0
    failed: int = 0
    passed: int = 0
    skipped: int = 0
    errors: int = 0
    xfailed: int = 0
    xpassed: int = 0
    collected: int = 0
    collection_failures: int = 0


class PytestCollectionFailure(BaseModel):
    """Model for a pytest collection failure."""

    model_config = ConfigDict(extra="allow")

    nodeid: str
    outcome: str = "failed"
    longrepr: Optional[str] = None


class PytestCrashInfo(BaseModel):
    """Model for pytest crash information."""

    model_config = ConfigDict(extra="allow")

    path: Optional[str] = None
    lineno: Optional[int] = None
    message: Optional[str] = None


class PytestTracebackEntry(BaseModel):
    """Model for a pytest traceback entry."""

    model_config = ConfigDict(extra="allow")

    path: Optional[str] = None
    lineno: Optional[int] = None
    message: Optional[str] = None


class PytestCallInfo(BaseModel):
    """Model for pytest call phase information."""

    model_config = ConfigDict(extra="allow")

    duration: Optional[float] = None
    outcome: str = "failed"
    crash: Optional[PytestCrashInfo] = None
    traceback: Optional[List[PytestTracebackEntry]] = None
    longrepr: Optional[str] = None


class PytestFailedTest(BaseModel):
    """Model for a failed pytest test."""

    model_config = ConfigDict(extra="allow")

    nodeid: str
    outcome: str = "failed"
    longrepr: Optional[str] = None
    duration: Optional[float] = None
    lineno: Optional[int] = None
    call: Optional[PytestCallInfo] = None
    setup: Optional[PytestCallInfo] = None
    teardown: Optional[PytestCallInfo] = None


class PytestResults(BaseModel):
    """Model for pytest results."""

    model_config = ConfigDict(extra="allow")

    summary: PytestSummary
    failed_collections: List[PytestCollectionFailure] = Field(default_factory=list)
    failed_tests: List[PytestFailedTest] = Field(default_factory=list)
    error: Optional[str] = None
