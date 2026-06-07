import importlib.util
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from paper_lattice.library import import_library, iter_library_files, summarize_import
from paper_lattice.storage import load_chunks, load_papers


def write_demo_files(root: Path) -> None:
    (root / "notes.md").write_text(
        "# Notes\n\nCPFEM validation with dislocation hardening.",
        encoding="utf-8",
    )
    (root / "refs.bib").write_text(
        """
@article{demo2026,
  title = {Demo Reference},
  author = {Ada Lattice},
  year = {2026},
  abstract = {Crystal plasticity validation with EBSD.}
}
""",
        encoding="utf-8",
    )
    (root / "ignore.csv").write_text("not,a,paper\n", encoding="utf-8")
    cache = root / "__pycache__"
    cache.mkdir()
    (cache / "cached.md").write_text("# Should not import", encoding="utf-8")


class LibraryImportTests(unittest.TestCase):
    def test_iter_library_files_filters_supported_files_and_cache_dirs(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_demo_files(root)
            files = [path.name for path in iter_library_files(root)]
            self.assertEqual(files, ["notes.md", "refs.bib"])

    def test_import_library_writes_papers_and_summary(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "library"
            root.mkdir()
            write_demo_files(root)
            workspace = Path(tmp) / "workspace"

            records = import_library(root, workspace=workspace)
            summary = summarize_import(records)

            self.assertEqual(summary["imported_files"], 2)
            self.assertEqual(summary["papers"], 2)
            self.assertEqual(summary["chunks"], 2)
            self.assertEqual(len(load_papers(workspace)), 2)
            self.assertEqual(len(load_chunks(workspace)), 2)

    def test_import_unsupported_file_is_skipped(self):
        with TemporaryDirectory() as tmp:
            source = Path(tmp) / "data.csv"
            source.write_text("x,y\n", encoding="utf-8")
            records = import_library(source, workspace=Path(tmp) / "workspace")
            self.assertEqual(records[0].status, "skipped")


@unittest.skipUnless(importlib.util.find_spec("fitz"), "PyMuPDF is needed to create the test PDF")
@unittest.skipUnless(importlib.util.find_spec("pypdf"), "pypdf is needed to ingest PDFs")
class LibraryPdfImportTests(unittest.TestCase):
    def test_import_library_accepts_pdf_files(self):
        from tests.test_pdf_ingest import make_pdf

        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "library"
            root.mkdir()
            make_pdf(root / "paper.pdf")
            workspace = Path(tmp) / "workspace"

            records = import_library(root, workspace=workspace)
            summary = summarize_import(records)

            self.assertEqual(summary["papers"], 1)
            chunks = load_chunks(workspace)
            self.assertEqual([chunk.metadata.get("page_start") for chunk in chunks], [1, 2])


if __name__ == "__main__":
    unittest.main()
