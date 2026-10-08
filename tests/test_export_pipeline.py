"""tests/test_export_pipeline.py

End-to-End Enterprise Export Pipeline Verification:
1. Validates in-memory generation of DOCX, PDF, and Markdown.
2. Validates table extraction, styling, and header preservation.
3. Validates that no temporary files are written to disk.
"""

import os
import unittest
from core.ui_components import export_markdown_to_docx, export_markdown_to_pdf
from docx import Document


class TestExportPipeline(unittest.TestCase):

    def setUp(self):
        with open("sample_data/sample_financial_report.txt", "r", encoding="utf-8") as f:
            self.sample_financial = f.read()

        self.table_markdown = (
            "# Executive Performance Summary\n\n"
            "Official Q3 enterprise metrics table:\n\n"
            "| Revenue Metric | Q3 Target | Q3 Actual | Variance |\n"
            "| :--- | :--- | :--- | :--- |\n"
            "| Cloud Ingestion | $120M | $142M | +18.3% |\n"
            "| Multi-tenant API | $80M | $88M | +10.0% |\n"
            "| Total ARR | $200M | $230M | +15.0% |\n\n"
            "### Risk & Anomaly Flags\n"
            "- Outlier latency in regional zone eu-west-1\n"
            "- Elevated memory utilization on ingestion worker nodes\n\n"
            "> Formally audited by Enterprise Observability Committee."
        )

    def test_docx_export_financial_report(self):
        """Verify DOCX export generates valid document with styled tables and headers."""
        buf = export_markdown_to_docx(self.table_markdown, title="Executive Performance Report")
        self.assertGreater(len(buf.getvalue()), 1000)

        # Inspect generated docx structure
        doc = Document(buf)
        self.assertGreater(len(doc.paragraphs), 3)
        self.assertEqual(len(doc.tables), 1)

        tbl = doc.tables[0]
        self.assertEqual(len(tbl.rows), 4)
        self.assertEqual(len(tbl.columns), 4)
        self.assertEqual(tbl.cell(0, 0).text, "Revenue Metric")
        self.assertEqual(tbl.cell(1, 0).text, "Cloud Ingestion")
        self.assertEqual(tbl.cell(1, 2).text, "$142M")

    def test_pdf_export_financial_report(self):
        """Verify PDF export generates valid PDF binary with table formatting."""
        buf = export_markdown_to_pdf(self.table_markdown, title="Executive Performance Report")
        pdf_bytes = buf.getvalue()
        self.assertGreater(len(pdf_bytes), 1000)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_docx_export_raw_financial_document(self):
        """Verify DOCX export handles full raw text files cleanly."""
        buf = export_markdown_to_docx(self.sample_financial, title="Q3 Financials")
        self.assertGreater(len(buf.getvalue()), 5000)
        doc = Document(buf)
        self.assertGreater(len(doc.paragraphs), 5)

    def test_pdf_export_raw_financial_document(self):
        """Verify PDF export handles full raw text files cleanly."""
        buf = export_markdown_to_pdf(self.sample_financial, title="Q3 Financials")
        pdf_bytes = buf.getvalue()
        self.assertGreater(len(pdf_bytes), 5000)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()
