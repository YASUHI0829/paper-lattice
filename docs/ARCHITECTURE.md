# PaperLattice Architecture

## Layer 1: Library

The library stores paper metadata and chunked text in JSONL files inside a local
workspace. JSONL is not the final storage layer, but it keeps the alpha easy to
inspect, version, and debug.

Files:

- `.paper_lattice/config.json`
- `.paper_lattice/papers.jsonl`
- `.paper_lattice/chunks.jsonl`

The batch importer scans mixed literature folders and routes files by extension:

- `.bib` through the BibTeX importer
- `.md`, `.markdown`, `.txt`, and `.pdf` through document ingest
- cache/build/workspace directories are skipped

PDF chunks store page metadata:

- `page_start`
- `page_end`
- `source_type: pdf`

## Layer 2: Retrieval

The MVP uses BM25 implemented with the Python standard library. This makes the
first release useful before vector search or API keys are configured.

Later retrieval modes:

- dense vector search
- hybrid BM25 plus vector ranking
- graph retrieval over paper cards
- metadata filters by year, material, method, or venue

## Layer 3: Structured Outputs

The `cards` command turns each paper into a domain-aware evidence card. The
`matrix` command turns ranked evidence into a table with one row per paper and
one column per domain field. The current extractor is heuristic and conservative:
fields become missing or `TODO` when no matching evidence is found, so weak
evidence stays visible instead of being smoothed into fake certainty.

When PDF page metadata is available, cells cite evidence as `chunk_id (p. N)`.

## Layer 4: Agents

The current agent layer is deterministic. It turns retrieved evidence into an
auditable research brief with explicit roles:

- scout
- retriever
- extractor
- synthesizer
- skeptic

The next implementation step is a provider interface where an LLM can fill
domain cards while preserving chunk IDs.

## Layer 5: Domain packs

Domain packs are versioned schemas. They describe what the software should
extract and compare for a research area.

The crystal plasticity pack defines:

- material systems
- crystal structures
- deformation mechanisms
- model families
- hardening laws
- validation targets
- limitations and assumptions

## Near-term web app

A small web interface exposes three panels:

- Library: imported papers and metadata.
- Evidence: ranked snippets with chunk IDs.
- Cards: domain-aware paper cards.
- Matrix: comparison tables and gap hints.

The alpha implementation uses Python's standard library HTTP server so the first
public demo has no extra deployment dependency. A later release can swap this for
FastAPI when the API surface becomes more stable.
