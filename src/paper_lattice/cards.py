from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .domain import load_domain_pack
from .evidence import chunk_ref, source_ref
from .matrix import candidate_segments, field_terms
from .models import Chunk, Paper
from .storage import load_chunks, load_papers


FIELD_ALIASES = {
    "title": ["title"],
    "material_system": ["material", "alloy", "steel", "ferritic", "bcc", "fcc", "hcp"],
    "processing_or_microstructure": ["microstructure", "grain", "texture", "ebsd", "orientation"],
    "crystal_structure": ["bcc", "fcc", "hcp", "crystal structure"],
    "deformation_mode": ["deformation", "dislocation", "slip", "twinning", "phase transformation"],
    "temperature_and_strain_rate": ["temperature", "strain rate", "strain-rate", "rate"],
    "model_family": ["cpfem", "crystal plasticity", "constitutive", "viscoplastic", "model"],
    "slip_or_twin_systems": ["slip system", "twin", "twinning"],
    "hardening_law": ["hardening", "slip resistance", "recovery", "forest"],
    "key_parameters": ["parameter", "initial slip resistance", "recovery", "forest", "hardening rate"],
    "equations": ["equation", "formula", "="],
    "calibration_data": ["calibration", "calibrated", "fit"],
    "validation_data": ["validation", "stress-strain", "ebsd", "texture", "local strain"],
    "main_claims": ["claim", "show", "demonstrate", "connect", "link", "suggest"],
    "assumptions": ["assumption", "assumptions", "simplified"],
    "limitations": ["limitation", "absence", "risk", "not transfer", "weakly constrained"],
    "reusable_dataset_or_code": ["dataset", "code", "repository", "available"],
    "research_question": ["question", "aim", "objective", "problem"],
    "method": ["method", "model", "simulation", "experiment", "approach"],
    "data_or_evidence": ["data", "evidence", "result", "validation", "figure"],
}


@dataclass(slots=True)
class CardEvidence:
    chunk: str
    source: str
    text: str

    def to_json(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class PaperCard:
    paper_id: str
    title: str
    source_path: str
    domain: str
    fields: dict[str, list[CardEvidence]] = field(default_factory=dict)
    missing_fields: list[str] = field(default_factory=list)

    def to_json(self) -> dict:
        payload = asdict(self)
        payload["fields"] = {
            key: [item.to_json() for item in value]
            for key, value in self.fields.items()
        }
        return payload


def terms_for_card_field(field_name: str) -> list[str]:
    normalized = field_name.strip().lower()
    terms = FIELD_ALIASES.get(normalized)
    if terms:
        return terms
    return field_terms(normalized.replace("_", " "))


def evidence_for_chunk_field(chunk: Chunk, field_name: str, max_items: int = 2) -> list[CardEvidence]:
    terms = terms_for_card_field(field_name)
    scored: list[tuple[int, CardEvidence]] = []
    for segment in candidate_segments(chunk.text):
        if segment.startswith("#"):
            segment = segment.lstrip("# ").strip()
            if not segment:
                continue
        lowered = segment.lower()
        label = lowered.split(":", 1)[0] if ":" in lowered else ""
        if label in {"authors", "year", "venue", "doi"}:
            continue
        hits = sum(1 for term in terms if term in lowered)
        if not hits:
            continue
        label_score = 0
        if lowered.startswith("abstract:"):
            label_score = 3
        elif lowered.startswith("keywords:"):
            label_score = 2
        scored.append(
            (
                hits + label_score,
                CardEvidence(
                    chunk=chunk_ref(chunk),
                    source=source_ref(chunk),
                    text=segment,
                ),
            )
        )
    scored.sort(key=lambda item: item[0], reverse=True)
    return [item for _, item in scored[:max_items]]


def title_evidence(paper: Paper) -> CardEvidence:
    return CardEvidence(
        chunk="metadata",
        source=paper.source_path,
        text=paper.title,
    )


def metadata_evidence(paper: Paper, key: str) -> CardEvidence | None:
    value = paper.metadata.get(key)
    if not value:
        return None
    return CardEvidence(chunk="metadata", source=paper.source_path, text=str(value))


def metadata_candidates(paper: Paper, field_name: str) -> list[CardEvidence]:
    if field_name == "title":
        return [title_evidence(paper)]
    if field_name in {"main_claims", "method", "data_or_evidence", "validation_data"}:
        evidence = metadata_evidence(paper, "abstract")
        return [evidence] if evidence else []
    if field_name in {"model_family", "material_system", "crystal_structure", "deformation_mode"}:
        evidence = metadata_evidence(paper, "keywords")
        return [evidence] if evidence else []
    return []


def build_paper_card(
    paper: Paper,
    chunks: list[Chunk],
    domain: str = "general",
    fields: list[str] | None = None,
) -> PaperCard:
    selected_fields = fields or load_domain_pack(domain).extraction_fields
    card = PaperCard(
        paper_id=paper.paper_id,
        title=paper.title,
        source_path=paper.source_path,
        domain=domain,
    )
    for field_name in selected_fields:
        field_evidence: list[CardEvidence] = metadata_candidates(paper, field_name)
        if field_name == "title":
            card.fields[field_name] = field_evidence
            continue
        for chunk in chunks:
            field_evidence.extend(evidence_for_chunk_field(chunk, field_name))
            if len(field_evidence) >= 3:
                break
        if field_evidence:
            card.fields[field_name] = field_evidence[:3]
        else:
            card.missing_fields.append(field_name)
    return card


def build_cards(
    workspace: str | Path | None = None,
    domain: str = "general",
    limit: int | None = None,
) -> list[PaperCard]:
    papers = load_papers(workspace)
    chunks = load_chunks(workspace)
    chunks_by_paper: dict[str, list[Chunk]] = {}
    for chunk in chunks:
        chunks_by_paper.setdefault(chunk.paper_id, []).append(chunk)
    cards = [
        build_paper_card(paper, chunks_by_paper.get(paper.paper_id, []), domain=domain)
        for paper in papers[:limit]
    ]
    return cards


def render_cards_markdown(cards: list[PaperCard]) -> str:
    lines = ["# PaperLattice Paper Cards", ""]
    if not cards:
        lines.append("No papers found.")
        return "\n".join(lines) + "\n"
    for card in cards:
        lines.append(f"## {card.title}")
        lines.append("")
        lines.append(f"- paper_id: `{card.paper_id}`")
        lines.append(f"- source: `{card.source_path}`")
        lines.append(f"- domain: `{card.domain}`")
        lines.append("")
        for field_name, evidence_items in card.fields.items():
            lines.append(f"### {field_name}")
            lines.append("")
            for item in evidence_items:
                lines.append(f"- `{item.chunk}` {item.text}")
                if item.source:
                    lines.append(f"  source: `{item.source}`")
            lines.append("")
        if card.missing_fields:
            lines.append("### missing_fields")
            lines.append("")
            lines.append(", ".join(f"`{field}`" for field in card.missing_fields))
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_cards_json(cards: list[PaperCard]) -> str:
    return json.dumps([card.to_json() for card in cards], indent=2, ensure_ascii=False) + "\n"
