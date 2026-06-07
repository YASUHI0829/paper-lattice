from __future__ import annotations

import textwrap

from .evidence import chunk_anchor, chunk_ref, source_ref
from .models import SearchHit


DOMAIN_LENSES = {
    "general": [
        "research question",
        "claim",
        "method",
        "data or evidence",
        "limitation",
        "follow-up question",
    ],
    "crystal_plasticity": [
        "material system",
        "crystal structure",
        "deformation mechanism",
        "constitutive model",
        "hardening law",
        "slip or twin system",
        "validation data",
        "open limitation",
    ],
}


def compact_snippet(text: str, width: int = 420) -> str:
    clean = " ".join(text.split())
    return textwrap.shorten(clean, width=width, placeholder="...")


def build_research_brief(query: str, hits: list[SearchHit], domain: str = "general") -> str:
    lens = DOMAIN_LENSES.get(domain, DOMAIN_LENSES["general"])
    lines: list[str] = []
    lines.append(f"# PaperLattice Brief: {query}")
    lines.append("")
    lines.append("## Agent Route")
    lines.append("")
    lines.append("1. Scout agent: expand the query into related mechanisms, methods, and terms.")
    lines.append("2. Retriever agent: collect ranked chunks and keep stable evidence IDs.")
    lines.append("3. Extractor agent: convert evidence into domain cards.")
    lines.append("4. Synthesizer agent: compare papers, group agreements, and surface gaps.")
    lines.append("5. Skeptic agent: flag weak evidence, missing controls, and citation gaps.")
    lines.append("")
    lines.append("## Domain Lens")
    lines.append("")
    for item in lens:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Evidence")
    lines.append("")
    if not hits:
        lines.append("No matching evidence was found. Ingest more papers or broaden the query.")
    for rank, hit in enumerate(hits, start=1):
        chunk = hit.chunk
        lines.append(f"### {rank}. {chunk.paper_title}")
        lines.append("")
        lines.append(f"- chunk: `{chunk_ref(chunk)}`")
        anchor = chunk_anchor(chunk)
        if anchor:
            lines.append(f"- anchor: `{anchor}`")
        lines.append(f"- score: `{hit.score:.3f}`")
        lines.append(f"- source: `{source_ref(chunk)}`")
        lines.append(f"- snippet: {compact_snippet(chunk.text)}")
        lines.append("")
    lines.append("## Next Synthesis Tasks")
    lines.append("")
    lines.append("- Build a comparison matrix with one row per paper and one column per domain field.")
    lines.append("- Extract exact parameter names, equations, and validation targets before summarizing.")
    lines.append("- Mark every generated claim with chunk IDs and unresolved evidence gaps.")
    lines.append("- Separate background consensus from claims that are specific to one material system.")
    return "\n".join(lines).rstrip() + "\n"
