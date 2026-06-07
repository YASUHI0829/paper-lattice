from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Iterator

from .models import Chunk, Paper


DEFAULT_WORKSPACE = ".paper_lattice"


def workspace_path(path: str | Path | None = None) -> Path:
    return Path(path or DEFAULT_WORKSPACE)


def init_workspace(
    path: str | Path | None = None,
    domain: str = "general",
    update_config: bool = False,
) -> Path:
    root = workspace_path(path)
    root.mkdir(parents=True, exist_ok=True)
    config_path = root / "config.json"
    if update_config or not config_path.exists():
        config_path.write_text(
            json.dumps({"domain": domain, "version": 1}, indent=2) + "\n",
            encoding="utf-8",
        )
    for name in ("papers.jsonl", "chunks.jsonl"):
        target = root / name
        if not target.exists():
            target.write_text("", encoding="utf-8")
    return root


def read_jsonl(path: Path) -> Iterator[dict]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_papers(root: str | Path | None = None) -> list[Paper]:
    ws = workspace_path(root)
    return [Paper(**row) for row in read_jsonl(ws / "papers.jsonl")]


def load_chunks(root: str | Path | None = None) -> list[Chunk]:
    ws = workspace_path(root)
    return [Chunk(**row) for row in read_jsonl(ws / "chunks.jsonl")]


def upsert_paper_and_chunks(
    paper: Paper,
    chunks: list[Chunk],
    root: str | Path | None = None,
) -> None:
    ws = workspace_path(root)
    init_workspace(ws)

    papers = {item.paper_id: item for item in load_papers(ws)}
    papers[paper.paper_id] = paper
    write_jsonl(ws / "papers.jsonl", [item.to_json() for item in papers.values()])

    old_chunks = [item for item in load_chunks(ws) if item.paper_id != paper.paper_id]
    all_chunks = old_chunks + chunks
    write_jsonl(ws / "chunks.jsonl", [item.to_json() for item in all_chunks])
