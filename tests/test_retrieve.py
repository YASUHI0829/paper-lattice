import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from paper_lattice.models import Chunk
from paper_lattice.retrieve import bm25_search, tokenize
from paper_lattice.storage import init_workspace


class RetrieveTests(unittest.TestCase):
    def test_tokenize_keeps_domain_terms(self):
        self.assertIn("cpfem", tokenize("CPFEM hardening model"))
        self.assertIn("strain-rate", tokenize("strain-rate sensitivity"))

    def test_bm25_ranks_matching_chunk(self):
        chunks = [
            Chunk(
                chunk_id="a",
                paper_id="p1",
                paper_title="Slip systems",
                source_path="demo",
                text="slip resistance hardening dislocation density",
                index=0,
            ),
            Chunk(
                chunk_id="b",
                paper_id="p2",
                paper_title="Other topic",
                source_path="demo",
                text="thermal conductivity and diffusion",
                index=0,
            ),
        ]
        hits = bm25_search("dislocation hardening", chunks, top_k=2)
        self.assertEqual(hits[0].chunk.chunk_id, "a")

    def test_init_workspace_keeps_existing_config(self):
        with TemporaryDirectory() as tmp:
            init_workspace(tmp, domain="crystal_plasticity")
            init_workspace(tmp)
            config = (Path(tmp) / "config.json").read_text(encoding="utf-8")
            self.assertIn("crystal_plasticity", config)

    def test_init_workspace_can_update_config_explicitly(self):
        with TemporaryDirectory() as tmp:
            init_workspace(tmp, domain="general")
            init_workspace(tmp, domain="crystal_plasticity", update_config=True)
            config = (Path(tmp) / "config.json").read_text(encoding="utf-8")
            self.assertIn("crystal_plasticity", config)


if __name__ == "__main__":
    unittest.main()
