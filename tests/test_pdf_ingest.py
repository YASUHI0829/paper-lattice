import importlib.util
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from paper_lattice.agents import build_research_brief
from paper_lattice.ingest import ingest_document
from paper_lattice.matrix import render_matrix
from paper_lattice.retrieve import search_workspace
from paper_lattice.storage import load_chunks
from paper_lattice.web import search_payload


def make_pdf(path: Path) -> None:
    import fitz

    doc = fitz.open()
    page1 = doc.new_page()
    page1.insert_text(
        (72, 72),
        "Synthetic PDF Crystal Plasticity\n"
        "Page one describes CPFEM validation with EBSD texture.",
    )
    page2 = doc.new_page()
    page2.insert_text(
        (72, 72),
        "Page two describes dislocation density hardening and slip resistance.",
    )
    doc.save(path)
    doc.close()


@unittest.skipUnless(importlib.util.find_spec("fitz"), "PyMuPDF is needed to create the test PDF")
@unittest.skipUnless(importlib.util.find_spec("pypdf"), "pypdf is needed to ingest PDFs")
class PdfIngestTests(unittest.TestCase):
    def test_pdf_ingest_keeps_page_anchors(self):
        with TemporaryDirectory() as tmp:
            pdf = Path(tmp) / "synthetic.pdf"
            workspace = Path(tmp) / "workspace"
            make_pdf(pdf)

            result = ingest_document(pdf, workspace=workspace)
            self.assertEqual(result.chunk_count, 2)

            chunks = load_chunks(workspace)
            pages = [chunk.metadata.get("page_start") for chunk in chunks]
            self.assertEqual(pages, [1, 2])

            hits = search_workspace("dislocation hardening", workspace=workspace)
            self.assertEqual(hits[0].chunk.metadata["page_start"], 2)

            brief = build_research_brief("dislocation hardening", hits)
            self.assertIn("p. 2", brief)
            self.assertIn("#page=2", brief)

            matrix = render_matrix("dislocation hardening", hits)
            self.assertIn("p. 2", matrix)

            payload = search_payload("dislocation hardening", workspace=workspace)
            self.assertEqual(payload["hits"][0]["anchor"], "p. 2")


if __name__ == "__main__":
    unittest.main()
