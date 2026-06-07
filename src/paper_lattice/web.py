from __future__ import annotations

import json
from html import escape
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .agents import compact_snippet
from .cards import build_cards, render_cards_markdown
from .evidence import chunk_anchor, source_ref
from .matrix import render_matrix
from .retrieve import search_workspace
from .storage import DEFAULT_WORKSPACE, init_workspace, load_chunks, load_papers


def paper_summary(workspace: str | Path | None = None) -> dict:
    papers = load_papers(workspace)
    chunks = load_chunks(workspace)
    chunk_counts: dict[str, int] = {}
    for chunk in chunks:
        chunk_counts[chunk.paper_id] = chunk_counts.get(chunk.paper_id, 0) + 1
    return {
        "paper_count": len(papers),
        "chunk_count": len(chunks),
        "papers": [
            {
                "paper_id": paper.paper_id,
                "title": paper.title,
                "doi": paper.doi,
                "year": paper.year,
                "source_path": paper.source_path,
                "chunk_count": chunk_counts.get(paper.paper_id, 0),
                "metadata": paper.metadata,
            }
            for paper in papers
        ],
    }


def search_payload(query: str, workspace: str | Path | None = None, top_k: int = 8) -> dict:
    hits = search_workspace(query, workspace=str(workspace) if workspace else None, top_k=top_k)
    return {
        "query": query,
        "hits": [
            {
                "rank": rank,
                "chunk_id": hit.chunk.chunk_id,
                "anchor": chunk_anchor(hit.chunk),
                "paper_title": hit.chunk.paper_title,
                "source_path": source_ref(hit.chunk),
                "score": round(hit.score, 3),
                "snippet": compact_snippet(hit.chunk.text, width=360),
            }
            for rank, hit in enumerate(hits, start=1)
        ],
    }


def matrix_payload(
    query: str,
    workspace: str | Path | None = None,
    domain: str = "general",
    top_k: int = 12,
) -> dict:
    hits = search_workspace(query, workspace=str(workspace) if workspace else None, top_k=top_k)
    return {
        "query": query,
        "domain": domain,
        "markdown": render_matrix(query, hits, domain=domain),
    }


def cards_payload(
    workspace: str | Path | None = None,
    domain: str = "general",
    limit: int | None = None,
) -> dict:
    cards = build_cards(workspace=workspace, domain=domain, limit=limit)
    return {
        "domain": domain,
        "paper_count": len(cards),
        "markdown": render_cards_markdown(cards),
    }


def json_response(handler: BaseHTTPRequestHandler, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def text_response(
    handler: BaseHTTPRequestHandler,
    body: str,
    content_type: str,
    status: HTTPStatus = HTTPStatus.OK,
) -> None:
    data = body.encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


def app_html(workspace: str | Path | None = None, domain: str = "general") -> str:
    title = "PaperLattice"
    safe_domain = escape(domain)
    safe_workspace = escape(str(workspace or DEFAULT_WORKSPACE))
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #17202a;
      --muted: #5d6673;
      --line: #d7dde5;
      --paper: #ffffff;
      --band: #f4f7f9;
      --accent: #0f766e;
      --accent-2: #7c3aed;
      --warn: #b45309;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      color: var(--ink);
      background: var(--band);
      letter-spacing: 0;
    }}
    header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 18px;
      min-height: 72px;
      padding: 14px 22px;
      border-bottom: 1px solid var(--line);
      background: var(--paper);
    }}
    h1 {{
      margin: 0;
      font-size: 22px;
      font-weight: 700;
    }}
    .meta {{
      display: flex;
      flex-wrap: wrap;
      justify-content: flex-end;
      gap: 10px;
      color: var(--muted);
      font-size: 13px;
    }}
    .shell {{
      display: grid;
      grid-template-columns: minmax(260px, 340px) minmax(0, 1fr);
      min-height: calc(100vh - 72px);
    }}
    aside {{
      border-right: 1px solid var(--line);
      background: #eef3f6;
      padding: 18px;
      overflow: auto;
    }}
    main {{
      padding: 18px 22px 28px;
      overflow: auto;
    }}
    .section-title {{
      margin: 0 0 10px;
      font-size: 15px;
      font-weight: 700;
    }}
    .stat-row {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
      margin-bottom: 16px;
    }}
    .stat {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--paper);
      padding: 10px;
    }}
    .stat strong {{
      display: block;
      font-size: 22px;
    }}
    .stat span {{
      color: var(--muted);
      font-size: 12px;
    }}
    .paper-list {{
      display: grid;
      gap: 10px;
    }}
    .paper {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--paper);
      padding: 11px;
    }}
    .paper h2 {{
      margin: 0 0 8px;
      font-size: 14px;
      line-height: 1.35;
    }}
    .paper p {{
      margin: 0;
      color: var(--muted);
      font-size: 12px;
      overflow-wrap: anywhere;
    }}
    .toolbar {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto auto;
      gap: 10px;
      margin-bottom: 16px;
    }}
    input, select, button {{
      height: 40px;
      border-radius: 8px;
      border: 1px solid var(--line);
      font: inherit;
    }}
    input, select {{
      min-width: 0;
      padding: 0 12px;
      background: var(--paper);
      color: var(--ink);
    }}
    button {{
      padding: 0 14px;
      background: var(--accent);
      border-color: var(--accent);
      color: white;
      font-weight: 700;
      cursor: pointer;
    }}
    button.secondary {{
      background: #243447;
      border-color: #243447;
    }}
    .tabs {{
      display: flex;
      gap: 8px;
      margin-bottom: 12px;
    }}
    .tab {{
      background: var(--paper);
      color: var(--ink);
      border-color: var(--line);
    }}
    .tab.active {{
      background: var(--accent-2);
      border-color: var(--accent-2);
      color: white;
    }}
    .panel {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--paper);
      min-height: 420px;
      padding: 14px;
    }}
    .hit {{
      border-bottom: 1px solid var(--line);
      padding: 12px 0;
    }}
    .hit:first-child {{ padding-top: 0; }}
    .hit:last-child {{ border-bottom: 0; }}
    .hit h3 {{
      margin: 0 0 7px;
      font-size: 15px;
    }}
    .hit .source {{
      color: var(--muted);
      font-size: 12px;
      overflow-wrap: anywhere;
    }}
    .score {{
      color: var(--warn);
      font-weight: 700;
    }}
    pre {{
      margin: 0;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      font-family: Consolas, Monaco, monospace;
      font-size: 12px;
      line-height: 1.5;
    }}
    .empty {{
      color: var(--muted);
      padding: 20px 0;
    }}
    @media (max-width: 860px) {{
      header {{
        align-items: flex-start;
        flex-direction: column;
      }}
      .meta {{ justify-content: flex-start; }}
      .shell {{
        grid-template-columns: 1fr;
      }}
      aside {{
        border-right: 0;
        border-bottom: 1px solid var(--line);
      }}
      .toolbar {{
        grid-template-columns: 1fr;
      }}
      button {{ width: 100%; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>PaperLattice</h1>
    <div class="meta">
      <span>workspace: {safe_workspace}</span>
      <span>domain: <strong>{safe_domain}</strong></span>
    </div>
  </header>
  <div class="shell">
    <aside>
      <h2 class="section-title">Library</h2>
      <div class="stat-row">
        <div class="stat"><strong id="paper-count">0</strong><span>papers</span></div>
        <div class="stat"><strong id="chunk-count">0</strong><span>chunks</span></div>
      </div>
      <div id="papers" class="paper-list"></div>
    </aside>
    <main>
      <div class="toolbar">
        <input id="query" value="Compare CPFEM and twinning plasticity validation" aria-label="Research query">
        <select id="domain" aria-label="Domain">
          <option value="general">general</option>
          <option value="crystal_plasticity" selected>crystal_plasticity</option>
        </select>
        <button id="run">Search</button>
      </div>
      <div class="tabs">
        <button class="tab active" id="tab-evidence">Evidence</button>
        <button class="tab" id="tab-cards">Cards</button>
        <button class="tab" id="tab-matrix">Matrix</button>
      </div>
      <section class="panel" id="evidence"></section>
      <section class="panel" id="cards" hidden><pre id="cards-output"></pre></section>
      <section class="panel" id="matrix" hidden><pre id="matrix-output"></pre></section>
    </main>
  </div>
  <script>
    const state = {{ active: "evidence" }};
    const paperCount = document.getElementById("paper-count");
    const chunkCount = document.getElementById("chunk-count");
    const papers = document.getElementById("papers");
    const query = document.getElementById("query");
    const domain = document.getElementById("domain");
    const evidence = document.getElementById("evidence");
    const cards = document.getElementById("cards");
    const matrix = document.getElementById("matrix");
    const cardsOutput = document.getElementById("cards-output");
    const matrixOutput = document.getElementById("matrix-output");
    const tabEvidence = document.getElementById("tab-evidence");
    const tabCards = document.getElementById("tab-cards");
    const tabMatrix = document.getElementById("tab-matrix");

    function escapeHtml(value) {{
      return String(value ?? "").replace(/[&<>"']/g, (char) => ({{
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
      }}[char]));
    }}

    function setTab(name) {{
      state.active = name;
      evidence.hidden = name !== "evidence";
      cards.hidden = name !== "cards";
      matrix.hidden = name !== "matrix";
      tabEvidence.classList.toggle("active", name === "evidence");
      tabCards.classList.toggle("active", name === "cards");
      tabMatrix.classList.toggle("active", name === "matrix");
    }}

    async function loadLibrary() {{
      const response = await fetch("/api/library");
      const data = await response.json();
      paperCount.textContent = data.paper_count;
      chunkCount.textContent = data.chunk_count;
      papers.innerHTML = data.papers.map((paper) => `
        <article class="paper">
          <h2>${{escapeHtml(paper.title)}}</h2>
          <p>${{paper.year ? escapeHtml(paper.year) + " - " : ""}}${{escapeHtml(paper.chunk_count)}} chunks</p>
          <p>${{escapeHtml(paper.doi || paper.source_path)}}</p>
        </article>
      `).join("") || '<p class="empty">No papers indexed.</p>';
    }}

    async function runSearch() {{
      const q = query.value.trim();
      if (!q) return;
      evidence.innerHTML = '<p class="empty">Searching...</p>';
      cardsOutput.textContent = "Building paper cards...";
      matrixOutput.textContent = "Building matrix...";
      const searchUrl = `/api/search?q=${{encodeURIComponent(q)}}&k=8`;
      const cardsUrl = `/api/cards?domain=${{encodeURIComponent(domain.value)}}&limit=8`;
      const matrixUrl = `/api/matrix?q=${{encodeURIComponent(q)}}&domain=${{encodeURIComponent(domain.value)}}&k=12`;
      const [searchResponse, cardsResponse, matrixResponse] = await Promise.all([fetch(searchUrl), fetch(cardsUrl), fetch(matrixUrl)]);
      const searchData = await searchResponse.json();
      const cardsData = await cardsResponse.json();
      const matrixData = await matrixResponse.json();
      evidence.innerHTML = searchData.hits.map((hit) => `
        <article class="hit">
          <h3>${{hit.rank}}. ${{escapeHtml(hit.paper_title)}} <span class="score">${{escapeHtml(hit.score)}}</span></h3>
          <p>${{escapeHtml(hit.snippet)}}</p>
          <p class="source">${{escapeHtml(hit.chunk_id)}}${{hit.anchor ? " - " + escapeHtml(hit.anchor) : ""}} - ${{escapeHtml(hit.source_path)}}</p>
        </article>
      `).join("") || '<p class="empty">No evidence found.</p>';
      cardsOutput.textContent = cardsData.markdown;
      matrixOutput.textContent = matrixData.markdown;
    }}

    tabEvidence.addEventListener("click", () => setTab("evidence"));
    tabCards.addEventListener("click", () => setTab("cards"));
    tabMatrix.addEventListener("click", () => setTab("matrix"));
    document.getElementById("run").addEventListener("click", runSearch);
    query.addEventListener("keydown", (event) => {{
      if (event.key === "Enter") runSearch();
    }});
    loadLibrary().then(runSearch);
  </script>
</body>
</html>
"""


class PaperLatticeHandler(BaseHTTPRequestHandler):
    workspace: str | Path | None = DEFAULT_WORKSPACE
    domain: str = "general"

    def log_message(self, format: str, *args: object) -> None:
        return

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)

        if parsed.path == "/":
            text_response(self, app_html(self.workspace, domain=self.domain), "text/html; charset=utf-8")
            return
        if parsed.path == "/api/library":
            json_response(self, paper_summary(self.workspace))
            return
        if parsed.path == "/api/search":
            q = query.get("q", [""])[0]
            top_k = int(query.get("k", ["8"])[0])
            json_response(self, search_payload(q, self.workspace, top_k=top_k))
            return
        if parsed.path == "/api/matrix":
            q = query.get("q", [""])[0]
            domain = query.get("domain", [self.domain])[0]
            top_k = int(query.get("k", ["12"])[0])
            json_response(self, matrix_payload(q, self.workspace, domain=domain, top_k=top_k))
            return
        if parsed.path == "/api/cards":
            domain = query.get("domain", [self.domain])[0]
            limit_value = query.get("limit", [""])[0]
            limit = int(limit_value) if limit_value else None
            json_response(self, cards_payload(self.workspace, domain=domain, limit=limit))
            return

        json_response(self, {"error": "not found"}, status=HTTPStatus.NOT_FOUND)


def serve(
    workspace: str | Path | None = DEFAULT_WORKSPACE,
    host: str = "127.0.0.1",
    port: int = 8765,
    domain: str = "general",
) -> ThreadingHTTPServer:
    init_workspace(workspace)
    handler = type(
        "ConfiguredPaperLatticeHandler",
        (PaperLatticeHandler,),
        {"workspace": workspace, "domain": domain},
    )
    server = ThreadingHTTPServer((host, port), handler)
    return server
