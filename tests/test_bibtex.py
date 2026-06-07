import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from paper_lattice.bibtex import ingest_bibtex, parse_bibtex
from paper_lattice.storage import load_chunks, load_papers


SAMPLE_BIBTEX = """
@article{demo2026,
  title = {Crystal Plasticity Demo},
  author = {Ada Lattice and Kai Slip},
  journal = {Demo Journal},
  year = {2026},
  doi = {10.0000/demo},
  abstract = {A BCC steel CPFEM model with dislocation density hardening.}
}

@inproceedings{second2026,
  title = {Second Demo},
  author = {Mira Twin},
  booktitle = {Demo Conference},
  year = {2026},
  abstract = {An HCP twinning model.}
}
"""


class BibtexTests(unittest.TestCase):
    def test_parse_bibtex_entry(self):
        entries = parse_bibtex(SAMPLE_BIBTEX)
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]["ID"], "demo2026")
        self.assertEqual(entries[0]["title"], "Crystal Plasticity Demo")
        self.assertEqual(entries[0]["year"], "2026")
        self.assertEqual(entries[1]["ID"], "second2026")

    def test_ingest_bibtex_creates_paper_and_chunk(self):
        with TemporaryDirectory() as tmp:
            source = Path(tmp) / "sample.bib"
            source.write_text(SAMPLE_BIBTEX, encoding="utf-8")
            results = ingest_bibtex(source, workspace=Path(tmp) / "workspace")
            self.assertEqual(len(results), 2)
            papers = load_papers(Path(tmp) / "workspace")
            chunks = load_chunks(Path(tmp) / "workspace")
            self.assertEqual(papers[0].doi, "10.0000/demo")
            self.assertIn("dislocation density hardening", chunks[0].text.lower())


if __name__ == "__main__":
    unittest.main()
