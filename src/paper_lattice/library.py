from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from .bibtex import ingest_bibtex
from .ingest import ingest_document


SUPPORTED_EXTENSIONS = {
    ".bib": "bibtex",
    ".md": "document",
    ".markdown": "document",
    ".txt": "document",
    ".pdf": "document",
}

SKIP_DIRS = {
    ".git",
    ".paper_lattice",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
}


@dataclass(slots=True)
class ImportRecord:
    path: str
    kind: str
    status: str
    paper_count: int = 0
    chunk_count: int = 0
    message: str = ""

    def to_json(self) -> dict:
        return asdict(self)


def is_supported(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_EXTENSIONS


def should_skip_dir(path: Path) -> bool:
    return path.name in SKIP_DIRS or path.name.startswith(".")


def iter_library_files(path: str | Path, recursive: bool = True) -> list[Path]:
    root = Path(path)
    if root.is_file():
        return [root]
    if not root.exists():
        raise FileNotFoundError(f"Import path does not exist: {root}")
    if not root.is_dir():
        raise ValueError(f"Import path is not a file or directory: {root}")

    found: list[Path] = []
    if recursive:
        for item in root.rglob("*"):
            if any(should_skip_dir(parent) for parent in item.parents if parent != root.parent):
                continue
            if item.is_file() and is_supported(item):
                found.append(item)
    else:
        for item in root.glob("*"):
            if item.is_file() and is_supported(item):
                found.append(item)
    return sorted(found, key=lambda item: str(item).lower())


def import_file(path: str | Path, workspace: str | Path | None = None) -> ImportRecord:
    source = Path(path)
    suffix = source.suffix.lower()
    kind = SUPPORTED_EXTENSIONS.get(suffix, "unsupported")
    if kind == "unsupported":
        return ImportRecord(
            path=str(source),
            kind=kind,
            status="skipped",
            message=f"Unsupported extension: {suffix or '(none)'}",
        )

    try:
        if kind == "bibtex":
            results = ingest_bibtex(source, workspace=workspace)
            return ImportRecord(
                path=str(source),
                kind=kind,
                status="imported",
                paper_count=len(results),
                chunk_count=sum(result.chunk_count for result in results),
            )

        result = ingest_document(source, workspace=workspace)
        return ImportRecord(
            path=str(source),
            kind=kind,
            status="imported",
            paper_count=1,
            chunk_count=result.chunk_count,
            message=result.paper.title,
        )
    except Exception as exc:  # pragma: no cover - exact dependency failures vary
        return ImportRecord(
            path=str(source),
            kind=kind,
            status="error",
            message=str(exc),
        )


def import_library(
    path: str | Path,
    workspace: str | Path | None = None,
    recursive: bool = True,
) -> list[ImportRecord]:
    files = iter_library_files(path, recursive=recursive)
    return [import_file(item, workspace=workspace) for item in files]


def summarize_import(records: list[ImportRecord]) -> dict:
    return {
        "files": len(records),
        "imported_files": sum(1 for record in records if record.status == "imported"),
        "skipped_files": sum(1 for record in records if record.status == "skipped"),
        "error_files": sum(1 for record in records if record.status == "error"),
        "papers": sum(record.paper_count for record in records if record.status == "imported"),
        "chunks": sum(record.chunk_count for record in records if record.status == "imported"),
        "records": [record.to_json() for record in records],
    }
