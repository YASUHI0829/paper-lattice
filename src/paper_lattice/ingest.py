from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

from .models import Chunk, IngestResult, Paper
from .storage import upsert_paper_and_chunks


@dataclass(slots=True)
class PageText:
    text: str
    page: int | None = None


def stable_id(*parts: str, length: int = 12) -> str:
    digest = hashlib.sha1("\n".join(parts).encode("utf-8")).hexdigest()
    return digest[:length]


def read_document(path: str | Path) -> str:
    return "\n\n".join(page.text for page in read_document_pages(path))


def read_document_pages(path: str | Path) -> list[PageText]:
    source = Path(path)
    suffix = source.suffix.lower()
    if suffix == ".pdf":
        return read_pdf_pages(source)
    return [PageText(text=source.read_text(encoding="utf-8", errors="replace"))]


def read_pdf(path: Path) -> str:
    return "\n\n".join(f"[page {page.page}]\n{page.text}" for page in read_pdf_pages(path))


def read_pdf_pages(path: Path) -> list[PageText]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError(
            "PDF ingest needs the optional dependency: pip install paper-lattice[pdf]"
        ) from exc

    reader = PdfReader(str(path))
    pages: list[PageText] = []
    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages.append(PageText(text=text, page=index))
    return pages


def infer_title(path: Path, text: str) -> str:
    for line in text.splitlines():
        clean = line.strip().lstrip("#").strip()
        if clean:
            return clean[:160]
    return path.stem


def clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(text: str, max_words: int = 220, overlap: int = 40) -> list[str]:
    words = text.split()
    if not words:
        return []
    if len(words) <= max_words:
        return [" ".join(words)]

    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = min(start + max_words, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start = max(end - overlap, start + 1)
    return chunks


def ingest_document(
    path: str | Path,
    workspace: str | Path | None = None,
    title: str | None = None,
    doi: str | None = None,
    year: int | None = None,
) -> IngestResult:
    source = Path(path).resolve()
    pages = read_document_pages(source)
    raw_text = "\n\n".join(page.text for page in pages)
    text = clean_text(raw_text)
    paper_title = title or infer_title(source, text)
    paper_id = stable_id(str(source), paper_title, text[:1000])
    paper = Paper(
        paper_id=paper_id,
        title=paper_title,
        source_path=str(source),
        doi=doi,
        year=year,
    )

    chunks = []
    for page in pages:
        page_text = clean_text(page.text)
        if not page_text:
            continue
        for chunk in chunk_text(page_text):
            chunk_id = f"{paper_id}-{len(chunks):04d}"
            metadata = {}
            if page.page is not None:
                metadata = {
                    "source_type": "pdf",
                    "page_start": page.page,
                    "page_end": page.page,
                }
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    paper_id=paper_id,
                    paper_title=paper_title,
                    source_path=str(source),
                    text=chunk,
                    index=len(chunks),
                    metadata=metadata,
                )
            )
    if not chunks and text:
        for chunk in chunk_text(text):
            chunk_id = f"{paper_id}-{len(chunks):04d}"
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    paper_id=paper_id,
                    paper_title=paper_title,
                    source_path=str(source),
                    text=chunk,
                    index=len(chunks),
                )
            )
    upsert_paper_and_chunks(paper, chunks, workspace)
    return IngestResult(paper=paper, chunk_count=len(chunks))
