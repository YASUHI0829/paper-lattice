# GitHub Launch Strategy

## Positioning

Use this one-line pitch:

> PaperLattice is an agentic RAG literature atlas that turns papers into
> evidence-backed method cards, comparison matrices, and research gap maps.

## What should be visible on day one

- A working CLI demo.
- A local web UI demo.
- A crystal plasticity domain pack.
- A synthetic example that avoids copyright issues.
- Clear architecture docs.
- A roadmap that invites contributors.

## What should be built before public launch

- Zotero or BibTeX import.
- Batch folder import with JSON reports.
- PDF ingest with page anchors.
- Domain-aware paper card export.
- Markdown and CSV export of comparison matrices.
- At least one browser screenshot or terminal GIF.
- GitHub Actions test workflow.
- MIT license and contribution guide.

## Good first issues

- Add a BibTeX importer.
- Add OpenAlex metadata enrichment.
- Add Semantic Scholar recommendations.
- Add a Streamlit or FastAPI web UI.
- Add a domain pack for biomedical papers.
- Add evaluation checks for citation coverage.

## Demo script

```powershell
paper-lattice init --domain crystal_plasticity
paper-lattice import-dir examples\demo_library --report examples\outputs\demo_library_import_report.json
paper-lattice cards --domain crystal_plasticity -o examples\outputs\crystal_plasticity_cards.md
paper-lattice brief "Compare CPFEM and dislocation-density hardening models" --domain crystal_plasticity
paper-lattice serve --domain crystal_plasticity
```

The demo should show that PaperLattice is not just summarizing. It is extracting
field-specific structure and preserving evidence IDs.
