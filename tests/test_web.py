import json
import threading
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.request import urlopen

from paper_lattice.ingest import ingest_document
from paper_lattice.web import app_html, cards_payload, paper_summary, search_payload, serve


class WebTests(unittest.TestCase):
    def test_payloads_expose_library_and_search(self):
        with TemporaryDirectory() as tmp:
            source = Path(tmp) / "note.md"
            source.write_text("# Demo\n\nCPFEM hardening validation with EBSD.", encoding="utf-8")
            workspace = Path(tmp) / "workspace"
            ingest_document(source, workspace=workspace)

            summary = paper_summary(workspace)
            self.assertEqual(summary["paper_count"], 1)
            self.assertEqual(summary["chunk_count"], 1)

            results = search_payload("CPFEM hardening", workspace=workspace)
            self.assertEqual(results["hits"][0]["paper_title"], "Demo")

    def test_app_html_contains_workbench_regions(self):
        html = app_html(".paper_lattice", domain="crystal_plasticity")
        self.assertIn("PaperLattice", html)
        self.assertIn('id="papers"', html)
        self.assertIn('id="cards-output"', html)
        self.assertIn('id="matrix-output"', html)

    def test_cards_payload_returns_markdown(self):
        with TemporaryDirectory() as tmp:
            source = Path(tmp) / "note.md"
            source.write_text("# Demo\n\nCPFEM validation with EBSD.", encoding="utf-8")
            workspace = Path(tmp) / "workspace"
            ingest_document(source, workspace=workspace)

            payload = cards_payload(workspace=workspace, domain="crystal_plasticity")
            self.assertEqual(payload["paper_count"], 1)
            self.assertIn("PaperLattice Paper Cards", payload["markdown"])

    def test_serve_library_endpoint(self):
        with TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            server = serve(workspace=workspace, port=0, domain="crystal_plasticity")
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                host, port = server.server_address
                with urlopen(f"http://{host}:{port}/api/library", timeout=5) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                self.assertEqual(payload["paper_count"], 0)
            finally:
                server.shutdown()
                server.server_close()


if __name__ == "__main__":
    unittest.main()
