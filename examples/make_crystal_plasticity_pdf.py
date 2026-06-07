from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent
PDF_PATH = ROOT / "crystal_plasticity_seed.pdf"
DEMO_LIBRARY_PDF_PATH = ROOT / "demo_library" / "crystal_plasticity_seed.pdf"
PNG_PATH = ROOT / "outputs" / "crystal_plasticity_seed_page1.png"
PNG_PAGE2_PATH = ROOT / "outputs" / "crystal_plasticity_seed_page2.png"


def main() -> None:
    try:
        import fitz
    except ImportError as exc:
        raise SystemExit("This helper needs PyMuPDF: python -m pip install pymupdf") from exc

    ROOT.joinpath("outputs").mkdir(parents=True, exist_ok=True)
    DEMO_LIBRARY_PDF_PATH.parent.mkdir(parents=True, exist_ok=True)
    doc = fitz.open()

    page1 = doc.new_page(width=595, height=842)
    page1.insert_text((72, 72), "Synthetic Crystal Plasticity PDF", fontsize=18)
    page1.insert_textbox(
        fitz.Rect(72, 118, 523, 170),
        "Page 1: A BCC ferritic steel CPFEM study links EBSD texture, "
        "stress-strain validation, and grain orientation statistics.",
        fontsize=11,
    )
    page1.insert_textbox(
        fitz.Rect(72, 190, 523, 222),
        "Evidence focus: material system, crystal structure, validation data.",
        fontsize=11,
    )

    page2 = doc.new_page(width=595, height=842)
    page2.insert_text((72, 72), "Dislocation-Density Hardening", fontsize=18)
    page2.insert_textbox(
        fitz.Rect(72, 118, 523, 170),
        "Page 2: The constitutive model uses dislocation density hardening, "
        "initial slip resistance, recovery, and forest hardening parameters.",
        fontsize=11,
    )
    page2.insert_textbox(
        fitz.Rect(72, 190, 523, 236),
        "Open limitation: the calibrated parameter set may not transfer across "
        "strain rates or heat treatments.",
        fontsize=11,
    )

    doc.save(PDF_PATH)
    doc.save(DEMO_LIBRARY_PDF_PATH)
    pix = doc[0].get_pixmap(matrix=fitz.Matrix(1.4, 1.4), alpha=False)
    pix.save(PNG_PATH)
    pix2 = doc[1].get_pixmap(matrix=fitz.Matrix(1.4, 1.4), alpha=False)
    pix2.save(PNG_PAGE2_PATH)
    doc.close()
    print(f"Wrote {PDF_PATH}")
    print(f"Wrote {DEMO_LIBRARY_PDF_PATH}")
    print(f"Wrote {PNG_PATH}")
    print(f"Wrote {PNG_PAGE2_PATH}")


if __name__ == "__main__":
    main()
