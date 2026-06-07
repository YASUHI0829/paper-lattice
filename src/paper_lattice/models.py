from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class Paper:
    paper_id: str
    title: str
    source_path: str
    doi: str | None = None
    year: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Chunk:
    chunk_id: str
    paper_id: str
    paper_title: str
    source_path: str
    text: str
    index: int
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SearchHit:
    chunk: Chunk
    score: float


@dataclass(slots=True)
class IngestResult:
    paper: Paper
    chunk_count: int
