import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from paper_lattice.cards import build_cards, render_cards_json, render_cards_markdown
from paper_lattice.domain import load_domain_pack, parse_list_block
from paper_lattice.ingest import ingest_document


class DomainPackTests(unittest.TestCase):
    def test_parse_list_block(self):
        text = """
name: demo
extraction_fields:
  - title
  - method
other:
  - ignored
"""
        self.assertEqual(parse_list_block(text, "extraction_fields"), ["title", "method"])

    def test_load_crystal_plasticity_pack(self):
        pack = load_domain_pack("crystal_plasticity")
        self.assertIn("material_system", pack.extraction_fields)
        self.assertIn("hardening_law", pack.extraction_fields)


class PaperCardTests(unittest.TestCase):
    def test_build_cards_extracts_domain_evidence(self):
        with TemporaryDirectory() as tmp:
            source = Path(tmp) / "paper.md"
            source.write_text(
                "# BCC CPFEM Study\n\n"
                "A BCC ferritic steel CPFEM model uses dislocation density hardening. "
                "Validation data include EBSD texture and stress-strain curves. "
                "The main limitation is transferability across strain rates.",
                encoding="utf-8",
            )
            workspace = Path(tmp) / "workspace"
            ingest_document(source, workspace=workspace)

            cards = build_cards(workspace=workspace, domain="crystal_plasticity")
            card = cards[0]

            self.assertEqual(card.title, "BCC CPFEM Study")
            self.assertIn("material_system", card.fields)
            self.assertIn("hardening_law", card.fields)
            self.assertIn("validation_data", card.fields)

            markdown = render_cards_markdown(cards)
            self.assertIn("PaperLattice Paper Cards", markdown)
            self.assertIn("hardening_law", markdown)

            data = json.loads(render_cards_json(cards))
            self.assertEqual(data[0]["domain"], "crystal_plasticity")
            self.assertIn("fields", data[0])


if __name__ == "__main__":
    unittest.main()
