from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field

from .agents import DOMAIN_LENSES, compact_snippet
from .evidence import chunk_ref
from .models import SearchHit


FIELD_TERMS = {
    "research question": ["question", "aim", "objective", "problem"],
    "claim": ["claim", "show", "demonstrate", "conclude", "suggest"],
    "method": ["method", "model", "simulation", "experiment", "approach"],
    "data or evidence": ["data", "evidence", "result", "validation", "figure"],
    "limitation": ["limitation", "assumption", "simplified", "absence", "risk"],
    "follow-up question": ["future", "open", "follow", "next"],
    "material system": ["material", "alloy", "steel", "magnesium", "aluminum", "ferritic"],
    "crystal structure": ["bcc", "fcc", "hcp", "crystal structure"],
    "deformation mechanism": ["deformation", "dislocation", "twin", "slip", "phase transformation"],
    "constitutive model": ["constitutive", "cpfem", "crystal plasticity", "viscoplastic", "model"],
    "hardening law": ["hardening", "slip resistance", "recovery", "forest"],
    "slip or twin system": ["slip system", "twin", "twinning"],
    "validation data": ["validation", "stress-strain", "ebsd", "texture", "lattice strain"],
    "open limitation": ["limitation", "assumption", "absence", "risk", "not transfer"],
}


@dataclass
class MatrixRow:
    paper_title: str
    source_path: str
    chunks: list[str] = field(default_factory=list)
    cells: dict[str, str] = field(default_factory=dict)


def field_terms(field_name: str) -> list[str]:
    return FIELD_TERMS.get(field_name, [field_name])


def candidate_segments(text: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []
    labeled = re.sub(
        r"\s+(?=(Title|Authors|Year|Venue|DOI|Keywords|Abstract|Note):)",
        "\n",
        normalized,
    )
    rough_segments = re.split(r"(?<=[.;])\s+|\n+", labeled)
    segments: list[str] = []
    for segment in rough_segments:
        segment = segment.strip()
        if not segment:
            continue
        if len(segment.split()) < 4:
            continue
        segments.append(segment)
    return segments or [normalized]


def evidence_for_field(hit: SearchHit, field_name: str) -> str | None:
    terms = field_terms(field_name)
    best_segment: str | None = None
    best_score = -1
    for segment in candidate_segments(hit.chunk.text):
        label_match = re.match(r"^(?P<label>[A-Za-z]+):", segment)
        label = label_match.group("label").lower() if label_match else ""
        if label in {"authors", "year", "venue", "doi"}:
            continue
        lowered = segment.lower()
        hits = sum(1 for term in terms if term in lowered)
        if not hits:
            continue
        score = hits
        if label == "abstract":
            score += 3
        elif label == "keywords":
            score += 2
        elif label == "title":
            score -= 1
        if score > best_score:
            best_score = score
            best_segment = segment
    if best_segment:
        return f"{compact_snippet(best_segment, width=180)} [{chunk_ref(hit.chunk)}]"
    return None


def build_matrix_rows(hits: list[SearchHit], domain: str = "general") -> tuple[list[str], list[MatrixRow]]:
    fields = DOMAIN_LENSES.get(domain, DOMAIN_LENSES["general"])
    rows_by_paper: dict[str, MatrixRow] = {}

    for hit in hits:
        chunk = hit.chunk
        row = rows_by_paper.setdefault(
            chunk.paper_id,
            MatrixRow(paper_title=chunk.paper_title, source_path=chunk.source_path),
        )
        ref = chunk_ref(chunk)
        if ref not in row.chunks:
            row.chunks.append(ref)
        for field_name in fields:
            if field_name in row.cells:
                continue
            evidence = evidence_for_field(hit, field_name)
            if evidence:
                row.cells[field_name] = evidence

    return fields, list(rows_by_paper.values())


def render_markdown_matrix(query: str, fields: list[str], rows: list[MatrixRow]) -> str:
    columns = ["paper", "evidence_chunks", *fields]
    lines = [f"# PaperLattice Matrix: {query}", ""]
    lines.append("| " + " | ".join(columns) + " |")
    lines.append("| " + " | ".join("---" for _ in columns) + " |")
    for row in rows:
        values = [
            row.paper_title,
            ", ".join(row.chunks),
            *[row.cells.get(field_name, "TODO") for field_name in fields],
        ]
        escaped = [value.replace("|", "\\|").replace("\n", " ") for value in values]
        lines.append("| " + " | ".join(escaped) + " |")
    if not rows:
        lines.append("| No matching evidence |  | " + " | ".join("TODO" for _ in fields) + " |")
    return "\n".join(lines) + "\n"


def render_csv_matrix(fields: list[str], rows: list[MatrixRow]) -> str:
    output = io.StringIO()
    columns = ["paper", "source", "evidence_chunks", *fields]
    writer = csv.DictWriter(output, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        record = {
            "paper": row.paper_title,
            "source": row.source_path,
            "evidence_chunks": ", ".join(row.chunks),
        }
        for field_name in fields:
            record[field_name] = row.cells.get(field_name, "")
        writer.writerow(record)
    return output.getvalue()


def render_matrix(
    query: str,
    hits: list[SearchHit],
    domain: str = "general",
    output_format: str = "markdown",
) -> str:
    fields, rows = build_matrix_rows(hits, domain=domain)
    if output_format == "csv":
        return render_csv_matrix(fields, rows)
    return render_markdown_matrix(query, fields, rows)
