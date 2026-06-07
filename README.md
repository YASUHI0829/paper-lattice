# PaperLattice

PaperLattice is an agentic RAG literature atlas for researchers who need more than
"chat with PDFs." It turns papers into searchable evidence, structured method
cards, and domain-aware review briefs.

The first domain pack targets crystal plasticity literature. The core design is
general: add a domain schema, import papers or notes, retrieve grounded evidence,
then ask specialist agents to produce synthesis plans, comparison matrices, and
gap maps.

## Why this project is different

- Evidence-first: every answer is built from ranked snippets and stable chunk IDs.
- Domain packs: reusable schemas define what matters in each research field.
- Agent workflow: planner, extractor, synthesizer, and skeptic roles are explicit.
- Local-first MVP: no API key is required for indexing and retrieval.
- GitHub-friendly demo path: crystal plasticity is the first high-signal showcase.

## Quickstart

```powershell
cd D:\Research\paper-lattice
python -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[pdf]"
paper-lattice init --domain crystal_plasticity
paper-lattice import-dir examples\demo_library --report examples\outputs\demo_library_import_report.json
paper-lattice search "dislocation density hardening"
paper-lattice brief "Compare CPFEM and dislocation-density hardening models"
paper-lattice cards --domain crystal_plasticity -o examples\outputs\crystal_plasticity_cards.md
paper-lattice matrix "Compare CPFEM and twinning plasticity validation" --domain crystal_plasticity
paper-lattice serve --domain crystal_plasticity
```

Example output:

- [Crystal plasticity comparison matrix](examples/outputs/crystal_plasticity_matrix.md)
- [CSV version](examples/outputs/crystal_plasticity_matrix.csv)
- [Crystal plasticity paper cards](examples/outputs/crystal_plasticity_cards.md)
- [Paper cards JSON](examples/outputs/crystal_plasticity_cards.json)
- [Batch import report](examples/outputs/demo_library_import_report.json)
- [Local web UI screenshot](examples/outputs/paper_lattice_web.png)
- [Synthetic PDF source](examples/crystal_plasticity_seed.pdf)
- [Synthetic PDF page 1 preview](examples/outputs/crystal_plasticity_seed_page1.png)
- [Synthetic PDF page 2 preview](examples/outputs/crystal_plasticity_seed_page2.png)

## PDF Page Anchors

PDF ingest is optional:

```powershell
.\.venv\Scripts\python -m pip install -e ".[pdf]"
paper-lattice ingest examples\crystal_plasticity_seed.pdf
paper-lattice brief "dislocation density hardening" --domain crystal_plasticity
```

PDF chunks preserve page anchors such as `p. 2`, so generated evidence can point
back to the source page.

For a no-install run from the checkout:

```powershell
$env:PYTHONPATH = "src"
python -m paper_lattice init --domain crystal_plasticity
python -m paper_lattice import-dir examples\demo_library --report examples\outputs\demo_library_import_report.json
python -m paper_lattice brief "Compare CPFEM and dislocation-density hardening models"
python -m paper_lattice serve --domain crystal_plasticity
```

Then open:

```text
http://127.0.0.1:8765
```

## Core concepts

PaperLattice separates the product into three layers.

1. Library layer: papers, notes, metadata, and text chunks.
2. Retrieval layer: reproducible local ranking over chunked evidence.
3. Agent layer: domain-aware workflows that turn evidence into useful research
   artifacts.

The current MVP uses a standard-library BM25 retriever so the repository stays
easy to run. Later versions can add vector search, graph retrieval, Zotero import,
OpenAlex/Semantic Scholar connectors, and LLM-backed synthesis.

Use `import-dir` for a Zotero-style working folder that contains exported BibTeX,
PDFs, Markdown notes, or plain text files.

Use `cards` to convert papers into domain-aware evidence cards before building a
comparison matrix.

## Crystal plasticity domain pack

The initial schema extracts:

- material system and crystal structure
- deformation mechanism
- constitutive model family
- slip or twin systems
- hardening law and parameters
- experiment or simulation validation data
- stress-strain targets and texture/microstructure descriptors
- assumptions, limitations, and open questions

This gives the project a concrete scientific demo without locking it to one field.

## Roadmap

- PDF parsing with figure and equation anchors
- PDF page anchors in evidence, briefs, matrices, and the web UI
- Zotero and BibTeX import
- batch folder import with JSON reports
- domain-aware paper cards
- evidence-backed comparison matrix export
- OpenAlex and Semantic Scholar metadata enrichment
- vector plus graph hybrid retrieval
- LLM provider adapters
- review matrix export to Markdown, CSV, and notebooks
- browser-based review workbench
- benchmark set for citation accuracy and evidence coverage

## Repository layout

```text
paper-lattice/
  src/paper_lattice/       Python package
  domain_packs/            Field-specific schemas
  examples/                Small demo inputs
  docs/                    Product and architecture notes
  tests/                   Unit tests
```

## Related ecosystem

PaperLattice is designed to complement, not replace, excellent tools such as
Zotero, PaperQA, LlamaIndex, OpenAlex, and Semantic Scholar. Its niche is the
research atlas layer: structured, domain-aware, evidence-grounded synthesis.
