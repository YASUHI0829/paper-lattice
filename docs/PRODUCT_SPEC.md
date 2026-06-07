# PaperLattice Product Spec

## Product thesis

Researchers do not only need PDF chat. They need a reproducible way to transform
papers into evidence-backed research structure: claims, methods, assumptions,
parameters, datasets, contradictions, and gaps.

PaperLattice is an agentic RAG literature atlas. It starts as a local-first tool
for importing papers and notes, retrieving evidence, and producing domain-aware
briefs. It can later grow into a full research workbench with graph retrieval,
LLM-backed extraction, and Zotero integration.

## Target users

- Graduate students starting a new literature review.
- Materials researchers comparing models and validation evidence.
- Research engineers who need auditable technical summaries.
- Any domain expert who wants reusable schema-driven literature analysis.

## MVP scope

- Local workspace with paper and chunk stores.
- Markdown, text, and optional PDF ingestion with page anchors.
- BibTeX metadata ingestion.
- Batch directory import for mixed literature folders.
- Reproducible BM25 evidence retrieval.
- Agent-style research brief generator.
- Domain-aware paper card generation.
- Domain-aware comparison matrix export.
- Local web UI for library browsing, search, and matrix preview.
- Crystal plasticity domain pack.
- Example data that is safe to ship in an open repository.

## Differentiation

Most tools answer questions over PDFs. PaperLattice should help build a research
map:

- What claims does each paper make?
- Which domain fields are supported or missing for each paper?
- Which equations and parameters support those claims?
- What evidence validates the method?
- Which page supports the retrieved evidence?
- Which claims transfer across materials or experimental conditions?
- Where are the contradictions and missing controls?

## Generality strategy

The core package should stay domain-agnostic. Domain knowledge enters through
versioned packs:

- extraction fields
- entity types
- starter queries
- specialist agent roles
- comparison matrix templates
- paper card templates
- evaluation checklists

Crystal plasticity is the first domain pack because it has rich structure:
materials, mechanisms, equations, calibration parameters, validation data, and
model assumptions.

## Star-oriented open-source packaging

- Start with a polished README and a runnable 60-second demo.
- Provide one specialized demo that looks genuinely useful.
- Keep the first install dependency-light.
- Add screenshots or GIFs after a small web UI exists.
- Publish example outputs in `examples/outputs/`.
- Include a local browser demo that runs without external services.
- Keep roadmap issues clear enough for outside contributors.
