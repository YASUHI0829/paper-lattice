from __future__ import annotations

import argparse
import json
from pathlib import Path

from .agents import build_research_brief
from .bibtex import ingest_bibtex
from .cards import build_cards, render_cards_json, render_cards_markdown
from .evidence import chunk_ref
from .ingest import ingest_document
from .library import import_library, summarize_import
from .matrix import render_matrix
from .retrieve import search_workspace
from .storage import DEFAULT_WORKSPACE, init_workspace
from .web import serve


def add_common_workspace(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--workspace",
        default=DEFAULT_WORKSPACE,
        help="PaperLattice workspace directory. Default: .paper_lattice",
    )


def cmd_init(args: argparse.Namespace) -> None:
    root = init_workspace(args.workspace, domain=args.domain, update_config=True)
    print(f"Initialized workspace: {root}")
    print(f"Domain: {args.domain}")


def cmd_ingest(args: argparse.Namespace) -> None:
    for item in args.paths:
        result = ingest_document(
            item,
            workspace=args.workspace,
            title=args.title,
            doi=args.doi,
            year=args.year,
        )
        print(f"Ingested {result.paper.title} ({result.chunk_count} chunks)")


def cmd_bibtex(args: argparse.Namespace) -> None:
    for item in args.paths:
        results = ingest_bibtex(item, workspace=args.workspace)
        for result in results:
            year = f", {result.paper.year}" if result.paper.year else ""
            print(f"Imported {result.paper.title}{year} ({result.chunk_count} chunks)")


def cmd_import_dir(args: argparse.Namespace) -> None:
    records = import_library(
        args.path,
        workspace=args.workspace,
        recursive=not args.no_recursive,
    )
    summary = summarize_import(records)
    print(
        "Imported "
        f"{summary['papers']} papers / {summary['chunks']} chunks "
        f"from {summary['imported_files']} files"
    )
    if summary["error_files"]:
        print(f"Errors: {summary['error_files']}")
    for record in records:
        if record.status == "imported":
            detail = f", {record.message}" if record.message else ""
            print(f"+ {record.kind}: {record.path} ({record.paper_count} papers, {record.chunk_count} chunks{detail})")
        elif args.show_skipped or record.status == "error":
            print(f"! {record.status}: {record.path} - {record.message}")
    if args.report:
        target = Path(args.report)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Wrote import report: {target}")


def cmd_search(args: argparse.Namespace) -> None:
    hits = search_workspace(args.query, workspace=args.workspace, top_k=args.top_k)
    for rank, hit in enumerate(hits, start=1):
        chunk = hit.chunk
        snippet = " ".join(chunk.text.split())[:320]
        print(f"{rank}. {chunk.paper_title}")
        print(f"   chunk={chunk_ref(chunk)} score={hit.score:.3f}")
        print(f"   {snippet}")


def cmd_brief(args: argparse.Namespace) -> None:
    hits = search_workspace(args.query, workspace=args.workspace, top_k=args.top_k)
    print(build_research_brief(args.query, hits, domain=args.domain))


def cmd_matrix(args: argparse.Namespace) -> None:
    hits = search_workspace(args.query, workspace=args.workspace, top_k=args.top_k)
    rendered = render_matrix(
        args.query,
        hits,
        domain=args.domain,
        output_format=args.format,
    )
    if args.output:
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered, encoding="utf-8")
        print(f"Wrote matrix: {target}")
    else:
        print(rendered)


def cmd_cards(args: argparse.Namespace) -> None:
    cards = build_cards(
        workspace=args.workspace,
        domain=args.domain,
        limit=args.limit,
    )
    if args.format == "json":
        rendered = render_cards_json(cards)
    else:
        rendered = render_cards_markdown(cards)
    if args.output:
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered, encoding="utf-8")
        print(f"Wrote paper cards: {target}")
    else:
        print(rendered)


def cmd_domains(args: argparse.Namespace) -> None:
    root = Path(__file__).resolve().parents[2] / "domain_packs"
    if not root.exists():
        print("No domain packs found.")
        return
    for path in sorted(root.glob("*")):
        if path.suffix.lower() in {".yaml", ".yml", ".json"}:
            print(path.name)


def cmd_serve(args: argparse.Namespace) -> None:
    server = serve(
        workspace=args.workspace,
        host=args.host,
        port=args.port,
        domain=args.domain,
    )
    print(f"Serving PaperLattice at http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping PaperLattice server.")
    finally:
        server.server_close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="paper-lattice",
        description="Agentic RAG literature atlas.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    init_parser = sub.add_parser("init", help="Create a local PaperLattice workspace.")
    add_common_workspace(init_parser)
    init_parser.add_argument("--domain", default="general", help="Initial domain pack name.")
    init_parser.set_defaults(func=cmd_init)

    ingest_parser = sub.add_parser("ingest", help="Ingest Markdown, text, or PDF documents.")
    add_common_workspace(ingest_parser)
    ingest_parser.add_argument("paths", nargs="+", help="Files to ingest.")
    ingest_parser.add_argument("--title", help="Override title. Best for one file at a time.")
    ingest_parser.add_argument("--doi", help="Optional DOI.")
    ingest_parser.add_argument("--year", type=int, help="Optional publication year.")
    ingest_parser.set_defaults(func=cmd_ingest)

    bibtex_parser = sub.add_parser("bibtex", help="Import BibTeX metadata as searchable paper records.")
    add_common_workspace(bibtex_parser)
    bibtex_parser.add_argument("paths", nargs="+", help="BibTeX files to import.")
    bibtex_parser.set_defaults(func=cmd_bibtex)

    import_dir_parser = sub.add_parser("import-dir", help="Import a folder of BibTeX, notes, text files, and PDFs.")
    add_common_workspace(import_dir_parser)
    import_dir_parser.add_argument("path", help="File or directory to import.")
    import_dir_parser.add_argument("--no-recursive", action="store_true", help="Only scan the top-level directory.")
    import_dir_parser.add_argument("--report", help="Optional JSON import report path.")
    import_dir_parser.add_argument("--show-skipped", action="store_true", help="Print skipped unsupported files.")
    import_dir_parser.set_defaults(func=cmd_import_dir)

    search_parser = sub.add_parser("search", help="Search indexed evidence.")
    add_common_workspace(search_parser)
    search_parser.add_argument("query", help="Search query.")
    search_parser.add_argument("-k", "--top-k", type=int, default=8)
    search_parser.set_defaults(func=cmd_search)

    brief_parser = sub.add_parser("brief", help="Create an agent-style research brief.")
    add_common_workspace(brief_parser)
    brief_parser.add_argument("query", help="Research question.")
    brief_parser.add_argument("--domain", default="general", help="Domain lens to apply.")
    brief_parser.add_argument("-k", "--top-k", type=int, default=8)
    brief_parser.set_defaults(func=cmd_brief)

    matrix_parser = sub.add_parser("matrix", help="Export a domain-aware paper comparison matrix.")
    add_common_workspace(matrix_parser)
    matrix_parser.add_argument("query", help="Research question or comparison topic.")
    matrix_parser.add_argument("--domain", default="general", help="Domain lens to apply.")
    matrix_parser.add_argument("--format", choices=["markdown", "csv"], default="markdown")
    matrix_parser.add_argument("-k", "--top-k", type=int, default=12)
    matrix_parser.add_argument("-o", "--output", help="Optional output path.")
    matrix_parser.set_defaults(func=cmd_matrix)

    cards_parser = sub.add_parser("cards", help="Generate domain-aware evidence cards for papers.")
    add_common_workspace(cards_parser)
    cards_parser.add_argument("--domain", default="general", help="Domain pack to use.")
    cards_parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    cards_parser.add_argument("--limit", type=int, help="Optional maximum number of papers.")
    cards_parser.add_argument("-o", "--output", help="Optional output path.")
    cards_parser.set_defaults(func=cmd_cards)

    domains_parser = sub.add_parser("domains", help="List bundled domain packs.")
    domains_parser.set_defaults(func=cmd_domains)

    serve_parser = sub.add_parser("serve", help="Run the local PaperLattice web UI.")
    add_common_workspace(serve_parser)
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8765)
    serve_parser.add_argument("--domain", default="general")
    serve_parser.set_defaults(func=cmd_serve)
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
