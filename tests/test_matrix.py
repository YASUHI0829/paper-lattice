import unittest

from paper_lattice.matrix import render_matrix
from paper_lattice.models import Chunk, SearchHit


class MatrixTests(unittest.TestCase):
    def test_render_crystal_plasticity_matrix(self):
        hit = SearchHit(
            chunk=Chunk(
                chunk_id="p1-0000",
                paper_id="p1",
                paper_title="BCC CPFEM",
                source_path="demo.md",
                text=(
                    "BCC ferritic steel uses a CPFEM constitutive model with "
                    "dislocation hardening. Validation data include stress-strain "
                    "curves and EBSD texture evolution."
                ),
                index=0,
            ),
            score=1.0,
        )
        rendered = render_matrix(
            "CPFEM validation",
            [hit],
            domain="crystal_plasticity",
            output_format="markdown",
        )
        self.assertIn("BCC CPFEM", rendered)
        self.assertIn("validation data", rendered)
        self.assertIn("p1-0000", rendered)

    def test_render_csv_matrix(self):
        hit = SearchHit(
            chunk=Chunk(
                chunk_id="p1-0000",
                paper_id="p1",
                paper_title="Paper",
                source_path="demo.md",
                text="The method uses simulation evidence.",
                index=0,
            ),
            score=1.0,
        )
        rendered = render_matrix("method", [hit], output_format="csv")
        self.assertIn("paper,source,evidence_chunks", rendered)
        self.assertIn("Paper,demo.md,p1-0000", rendered)


if __name__ == "__main__":
    unittest.main()
