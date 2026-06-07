from __future__ import annotations

import re
from pathlib import Path

from .ingest import chunk_text, clean_text, stable_id
from .models import Chunk, IngestResult, Paper
from .storage import upsert_paper_and_chunks


ENTRY_START_RE = re.compile(r"@(?P<type>[A-Za-z]+)\s*(?P<brace>[{(])\s*(?P<key>[^,\s]+)\s*,")


def strip_outer_value(value: str) -> str:
    value = value.strip().rstrip(",").strip()
    if len(value) >= 2 and value[0] == "{" and value[-1] == "}":
        value = value[1:-1]
    elif len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        value = value[1:-1]
    value = value.replace("\n", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def split_bibtex_entries(text: str) -> list[str]:
    entries: list[str] = []
    index = 0
    while True:
        match = ENTRY_START_RE.search(text, index)
        if not match:
            break
        start = match.start()
        open_char = match.group("brace")
        close_char = "}" if open_char == "{" else ")"
        depth = 0
        cursor = match.start("brace")
        while cursor < len(text):
            char = text[cursor]
            if char == open_char:
                depth += 1
            elif char == close_char:
                depth -= 1
                if depth == 0:
                    entries.append(text[start : cursor + 1])
                    index = cursor + 1
                    break
            cursor += 1
        else:
            entries.append(text[start:])
            break
    return entries


def parse_entry(entry: str) -> dict[str, str]:
    header = ENTRY_START_RE.search(entry)
    if not header:
        return {}
    fields: dict[str, str] = {
        "ENTRYTYPE": header.group("type").lower(),
        "ID": header.group("key").strip(),
    }
    body = entry[header.end() :].strip()
    if body.endswith(("}", ")")):
        body = body[:-1]

    cursor = 0
    while cursor < len(body):
        while cursor < len(body) and body[cursor] in " \t\r\n,":
            cursor += 1
        name_start = cursor
        while cursor < len(body) and re.match(r"[A-Za-z0-9_\-]", body[cursor]):
            cursor += 1
        if cursor == name_start:
            break
        field_name = body[name_start:cursor].lower()
        while cursor < len(body) and body[cursor].isspace():
            cursor += 1
        if cursor >= len(body) or body[cursor] != "=":
            break
        cursor += 1
        while cursor < len(body) and body[cursor].isspace():
            cursor += 1
        value_start = cursor
        if cursor < len(body) and body[cursor] in "{(":
            open_char = body[cursor]
            close_char = "}" if open_char == "{" else ")"
            depth = 0
            while cursor < len(body):
                if body[cursor] == open_char:
                    depth += 1
                elif body[cursor] == close_char:
                    depth -= 1
                    if depth == 0:
                        cursor += 1
                        break
                cursor += 1
        elif cursor < len(body) and body[cursor] == '"':
            cursor += 1
            escaped = False
            while cursor < len(body):
                char = body[cursor]
                if char == "\\" and not escaped:
                    escaped = True
                    cursor += 1
                    continue
                if char == '"' and not escaped:
                    cursor += 1
                    break
                escaped = False
                cursor += 1
        else:
            while cursor < len(body) and body[cursor] != ",":
                cursor += 1
        fields[field_name] = strip_outer_value(body[value_start:cursor])
    return fields


def parse_bibtex(text: str) -> list[dict[str, str]]:
    return [fields for fields in (parse_entry(entry) for entry in split_bibtex_entries(text)) if fields]


def paper_text_from_bibtex(fields: dict[str, str]) -> str:
    labels = [
        ("title", "Title"),
        ("author", "Authors"),
        ("year", "Year"),
        ("journal", "Venue"),
        ("booktitle", "Venue"),
        ("doi", "DOI"),
        ("keywords", "Keywords"),
        ("abstract", "Abstract"),
        ("note", "Note"),
    ]
    lines = [f"# {fields.get('title', fields.get('ID', 'Untitled'))}"]
    for key, label in labels:
        value = fields.get(key)
        if value:
            lines.append(f"{label}: {value}")
    return clean_text("\n".join(lines))


def ingest_bibtex(
    path: str | Path,
    workspace: str | Path | None = None,
) -> list[IngestResult]:
    source = Path(path).resolve()
    entries = parse_bibtex(source.read_text(encoding="utf-8", errors="replace"))
    results: list[IngestResult] = []
    for fields in entries:
        title = fields.get("title", fields.get("ID", "Untitled"))
        year = int(fields["year"]) if fields.get("year", "").isdigit() else None
        paper_id = stable_id("bibtex", fields.get("ID", ""), title, fields.get("doi", ""))
        metadata = {
            "bibtex_key": fields.get("ID"),
            "entry_type": fields.get("ENTRYTYPE"),
            "authors": fields.get("author"),
            "venue": fields.get("journal") or fields.get("booktitle"),
            "keywords": fields.get("keywords"),
            "abstract": fields.get("abstract"),
        }
        paper = Paper(
            paper_id=paper_id,
            title=title,
            source_path=str(source),
            doi=fields.get("doi"),
            year=year,
            metadata={key: value for key, value in metadata.items() if value},
        )
        text = paper_text_from_bibtex(fields)
        chunks = [
            Chunk(
                chunk_id=f"{paper_id}-{index:04d}",
                paper_id=paper_id,
                paper_title=title,
                source_path=str(source),
                text=chunk,
                index=index,
                metadata={"source_type": "bibtex", "bibtex_key": fields.get("ID")},
            )
            for index, chunk in enumerate(chunk_text(text))
        ]
        upsert_paper_and_chunks(paper, chunks, workspace)
        results.append(IngestResult(paper=paper, chunk_count=len(chunks)))
    return results
