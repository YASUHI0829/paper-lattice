from __future__ import annotations

from .models import Chunk


def chunk_anchor(chunk: Chunk) -> str | None:
    page_start = chunk.metadata.get("page_start")
    page_end = chunk.metadata.get("page_end", page_start)
    if page_start is None:
        return None
    if page_end is None or page_end == page_start:
        return f"p. {page_start}"
    return f"pp. {page_start}-{page_end}"


def chunk_ref(chunk: Chunk) -> str:
    anchor = chunk_anchor(chunk)
    if anchor:
        return f"{chunk.chunk_id} ({anchor})"
    return chunk.chunk_id


def source_ref(chunk: Chunk) -> str:
    page_start = chunk.metadata.get("page_start")
    page_end = chunk.metadata.get("page_end", page_start)
    if page_start is not None:
        if page_end is not None and page_end != page_start:
            return f"{chunk.source_path}#pages={page_start}-{page_end}"
        return f"{chunk.source_path}#page={page_start}"
    return chunk.source_path
