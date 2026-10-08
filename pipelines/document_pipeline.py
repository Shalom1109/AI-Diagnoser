"""pipelines/document_pipeline.py

Document extraction, parsing, summarization, and interactive Q&A pipeline.
Supports:
1. PDF documents (via pypdf) with page-by-page extraction.
2. Microsoft Word (.docx) documents (via python-docx).
3. Plain text and Markdown (.txt, .md).
4. Generative & Extractive multi-tier summarization (Executive Brief, Key Takeaways, Deep Dive).
5. Interactive Ask-the-Document Q&A engine connecting to `core.llm_router.query_llm`.
"""

import io
import math
import os
import re
from typing import Any, Dict, List, Optional, Tuple

import docx
import pypdf

from core.llm_router import query_llm


# ---------------------------------------------------------------------------
# 1. Document Ingestion & Text Extraction
# ---------------------------------------------------------------------------
def _extract_from_pdf(file_bytes: bytes) -> Tuple[str, List[str]]:
    """Extract full text and individual page strings from PDF bytes."""
    reader = pypdf.PdfReader(io.BytesIO(file_bytes))
    pages_text = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        pages_text.append(text.strip())
    full_text = "\n\n--- Page Break ---\n\n".join(pages_text)
    return full_text, pages_text


def _extract_from_docx(file_bytes: bytes) -> Tuple[str, List[str]]:
    """Extract paragraphs and text from Microsoft Word .docx bytes."""
    doc = docx.Document(io.BytesIO(file_bytes))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    # Also extract text from tables
    table_texts = []
    for table in doc.tables:
        for row in table.rows:
            row_data = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if row_data:
                table_texts.append(" | ".join(row_data))

    combined_sections = paragraphs + (["\n--- Tables ---"] + table_texts if table_texts else [])
    full_text = "\n\n".join(combined_sections)
    return full_text, combined_sections


def _extract_from_txt(file_bytes: bytes) -> Tuple[str, List[str]]:
    """Extract text from plain text or markdown bytes with encoding fallback."""
    for encoding in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
        try:
            text = file_bytes.decode(encoding)
            paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
            return text, paragraphs
        except UnicodeDecodeError:
            continue
    text = file_bytes.decode("utf-8", errors="replace")
    return text, [text]


def resolve_file_bytes(file_source: Any) -> bytes:
    """Safely converts file uploads, paths, or byte streams into raw bytes."""
    if hasattr(file_source, "getvalue"):
        return file_source.getvalue()
    elif hasattr(file_source, "read"):
        content = file_source.read()
        if hasattr(file_source, "seek"):
            file_source.seek(0)
        return content
    elif isinstance(file_source, str) and os.path.isfile(file_source):
        with open(file_source, "rb") as f:
            return f.read()
    elif isinstance(file_source, (bytes, bytearray)):
        return bytes(file_source)
    raise ValueError(f"Unsupported file source type: {type(file_source)}")


def load_document(file_source: Any, filename: str) -> Dict[str, Any]:
    """Load and parse document content from a Streamlit UploadedFile or bytes.

    Returns:
        dict containing:
        - filename: str
        - file_type: 'PDF', 'DOCX', 'TXT'
        - full_text: complete extracted text
        - pages_or_chunks: list of strings (pages or paragraph blocks)
        - page_count: int
        - word_count: int
        - char_count: int
        - reading_time_min: float
    """
    file_bytes = resolve_file_bytes(file_source)
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".pdf":
        full_text, chunks = _extract_from_pdf(file_bytes)
        file_type = "PDF"
        page_count = len(chunks)
    elif ext in (".docx", ".doc"):
        full_text, chunks = _extract_from_docx(file_bytes)
        file_type = "DOCX"
        # Estimate page count (~400 words per page)
        words = len(full_text.split())
        page_count = max(1, math.ceil(words / 400))
    else:
        full_text, chunks = _extract_from_txt(file_bytes)
        file_type = "TXT"
        words = len(full_text.split())
        page_count = max(1, math.ceil(words / 400))

    words = len(full_text.split())
    char_count = len(full_text)
    # Average adult reading speed: ~220 words per minute
    reading_time = round(max(0.5, words / 220.0), 1)

    return {
        "filename": filename,
        "file_type": file_type,
        "full_text": full_text,
        "pages_or_chunks": chunks,
        "page_count": page_count,
        "word_count": words,
        "char_count": char_count,
        "reading_time_min": reading_time
    }


# ---------------------------------------------------------------------------
# 2. Summarization Engine & Prompt Templates
# ---------------------------------------------------------------------------
SUMMARY_PROMPT_TEMPLATE = """You are a precise Document Intelligence Engine. Analyze the provided document text and extract factual data only. Do NOT write a narrative or a story.

Structure your response strictly using these exact sections:
1. **Executive Summary**: 2-3 concise sentences summarizing the core document purpose.
2. **Key Insights**: 
   - [Key finding 1 with specific data/metrics if available]
   - [Key finding 2]
   - [Key finding 3]
3. **Core Entities & Metrics**: Bullet points listing key numbers, dates, organizations, or financial metrics found in the text.
4. **Document Q&A Context**: Summary of the main topics available for user querying.

Document Text:
{document_text}"""


QA_PROMPT_TEMPLATE = """You are an expert document assistant. Answer the user's query strictly based on the provided document context. 
- If the answer is present in the document, provide a clear, direct answer with bullet points if applicable.
- Do NOT invent information or write a story. 
- If the answer is not in the document, state: "The provided document does not contain information regarding this query."

Document Context:
{document_text}

User Query:
{user_query}"""


STRUCTURED_JSON_EXTRACTION_PROMPT = """You are an expert Enterprise Document Intelligence Engine. Analyze the provided document/image with high precision.

Extract all information strictly conforming to the following schema and rules:
1. Extract all visible text, maintaining structural hierarchy (headers, key-value pairs, line items, footnotes).
2. For tables, reconstruct them as structured JSON objects.
3. Perform currency, date (YYYY-MM-DD), and numerical normalization where applicable.
4. If a value is partially obscured or unreadable, flag it with "[UNCERTAIN]" instead of guessing.

Return ONLY a valid JSON payload with this exact structure:
{
  "document_type": "invoice | form | receipt | contract | report | unknown",
  "metadata": {
    "title": "string",
    "date": "YYYY-MM-DD",
    "identifier_number": "string"
  },
  "key_entities": {
    "sender": {},
    "recipient": {}
  },
  "line_items": [
    { "description": "string", "quantity": 0, "unit_price": 0.0, "total": 0.0 }
  ],
  "totals": {
    "subtotal": 0.0,
    "tax": 0.0,
    "total": 0.0,
    "currency": "string"
  },
  "confidence_score": 0.95
}

Document Text:
{document_text}"""


SUMMARY_PROMPTS = {
    "executive": SUMMARY_PROMPT_TEMPLATE,
    "json_schema": STRUCTURED_JSON_EXTRACTION_PROMPT,
    "key_takeaways": (
        "You are a precise Document Intelligence Engine. Extract factual key takeaways and quantitative metrics only. Do NOT write a narrative or story.\n\n"
        "Structure your response strictly using these sections:\n"
        "1. **Critical Takeaways**: Core essential bullet points\n"
        "2. **Key Data Points & Quantitative Evidence**: Specific figures, dates, percentages\n"
        "3. **Actionable Tasks & Next Steps**: Specific directives or owner tasks\n\n"
        "Document Text:\n{document_text}"
    ),
    "deep_dive": (
        "You are a precise Document Intelligence Engine. Provide a comprehensive, section-by-section factual synthesis. Do NOT write a narrative or story.\n\n"
        "Structure your response strictly using these sections:\n"
        "1. **Executive Summary**: 2-3 concise sentences summarizing core purpose.\n"
        "2. **Section-by-Section Breakdown**: High-impact insights by domain.\n"
        "3. **Core Entities, Metrics & Risk Factors**: Key data, financial anchors, and risks.\n"
        "4. **Document Q&A Context**: Summary of main topics available for user querying.\n\n"
        "Document Text:\n{document_text}"
    )
}


def generate_document_summary(
    doc_text: str,
    summary_type: str = "executive",
    model_provider: str = "Google Gemini",
    model_name: str = "gemini-3.8-flash",
    api_key: Optional[str] = None,
    **kwargs
) -> str:
    """Generate structured summary from document text using the LLM router."""
    if not doc_text.strip():
        return "⚠️ Document text is empty. Please upload a valid document."

    # Truncate text if excessively long to prevent token overflow on smaller models
    max_chars = 35000
    truncated_text = doc_text[:max_chars]
    if len(doc_text) > max_chars:
        truncated_text += f"\n\n[... Note: Text truncated from {len(doc_text)} characters for context efficiency ...]"

    if summary_type == "executive" or summary_type not in SUMMARY_PROMPTS:
        final_prompt = SUMMARY_PROMPT_TEMPLATE.format(document_text=truncated_text)
    else:
        template = SUMMARY_PROMPTS[summary_type]
        if "{document_text}" in template:
            final_prompt = template.format(document_text=truncated_text)
        else:
            final_prompt = f"{template}\n\n{truncated_text}"

    return query_llm(
        prompt=final_prompt,
        model_provider=model_provider,
        model_name=model_name,
        api_key=api_key,
        **kwargs
    )


# ---------------------------------------------------------------------------
# 3. Interactive Ask-the-Document Q&A
# ---------------------------------------------------------------------------
def ask_document_question(
    doc_text: str,
    question: str,
    model_provider: str = "Google Gemini",
    model_name: str = "gemini-3.8-flash",
    api_key: Optional[str] = None,
    **kwargs
) -> str:
    """Query the document text to answer a specific user question using QA_PROMPT_TEMPLATE."""
    if not question.strip():
        return "Please enter a valid question."

    # Keep relevant portion of document text
    max_chars = 30000
    truncated_text = doc_text[:max_chars]

    prompt = QA_PROMPT_TEMPLATE.format(
        document_text=truncated_text,
        user_query=question.strip()
    )

    return query_llm(
        prompt=prompt,
        model_provider=model_provider,
        model_name=model_name,
        api_key=api_key,
        **kwargs
    )


def export_summary_markdown(
    filename: str,
    summary_content: str,
    metadata: Dict[str, Any]
) -> str:
    """Prepare a downloadable Markdown file containing document metadata and analysis."""
    header = (
        f"# Document Intelligence Report: {filename}\n"
        f"**File Type**: {metadata.get('file_type', 'Document')} | "
        f"**Pages/Sections**: {metadata.get('page_count', 1)} | "
        f"**Word Count**: {metadata.get('word_count', 0):,} words | "
        f"**Est. Reading Time**: {metadata.get('reading_time_min', 0)} mins\n\n"
        f"---\n\n"
    )
    return header + summary_content
