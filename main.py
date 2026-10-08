"""main.py

Multimodal Document Intelligence Studio
Minimalist Architectural Aesthetic:
- Pure Apple SF Pro Typography & dynamic Dark Glass / Porcelain Theme.
- Top-Right Dark Mode Toggle.
- Hardcoded Google Gemini (gemini-2.5-flash) intelligence engine.
- Clean 2-Tab Interface: Document Studio, Vision Intelligence.
- Stateful Claude Artifact Workspace with version rollback, visual diffing, and multi-format export.
"""

import os
import streamlit as st

from core.styles import inject_clean_theme, apply_custom_theme
from core.llm_router import LLMRouter
from core.ui_components import (
    render_image_diagnostics_panel,
    set_initial_artifact,
    render_claude_artifact_workspace,
    export_markdown_to_docx,
    export_markdown_to_pdf,
)
from pipelines.document_pipeline import (
    ask_document_question,
    generate_document_summary,
    load_document,
)
from pipelines.image_pipeline import (
    analyze_image_with_llm,
    extract_dominant_colors,
    extract_image_metadata,
    load_image,
)

# ---------------------------------------------------------------------------
# Streamlit Application Configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Multimodal Document Intelligence",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------------------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------------------------
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "Dark" if st.session_state.dark_mode else "Light"

if "model_provider" not in st.session_state:
    st.session_state.model_provider = "Google Gemini"

if "doc_result" not in st.session_state:
    st.session_state.doc_result = ""

if "vision_result" not in st.session_state:
    st.session_state.vision_result = ""

# Permanent Default AI Agent: Google Gemini
selected_provider = "Google Gemini"
selected_model = "gemini-2.5-flash"
api_key_input = None
ollama_base_url = None

router = LLMRouter()

# ---------------------------------------------------------------------------
# Top Header Row: Branding & Top-Right Dark Mode Toggle
# ---------------------------------------------------------------------------
header_col1, header_col2 = st.columns([3.8, 1.2], vertical_alignment="center")

with header_col1:
    st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 14px; flex-wrap: wrap; margin-bottom: 6px;">
            <h1 style="margin: 0; font-size: 2.15rem; font-weight: 600; letter-spacing: -0.03em;">
                <span class="brand-title">Multimodal Document Intelligence</span>
            </h1>
            <span class="status-badge badge-amber" style="font-size: 0.84rem; padding: 4px 12px; font-weight: 600;">
                ✦ Powered by Gemini
            </span>
        </div>
        <p style="color: var(--secondary-text-color); font-size: 0.96rem; line-height: 1.5; margin: 0; font-weight: 400; max-width: 820px;">
            Executive intelligence studio for multi-format document synthesis, computer vision OCR, and structured diagnostics.
        </p>
        """,
        unsafe_allow_html=True
    )

with header_col2:
    is_dark = st.toggle("🌙 Dark Mode", value=st.session_state.dark_mode, key="app_theme_toggle")
    if is_dark != st.session_state.dark_mode:
        st.session_state.dark_mode = is_dark
        st.session_state.theme_mode = "Dark" if is_dark else "Light"
        st.rerun()

# Inject Dynamic Theme CSS
inject_clean_theme(dark_mode=st.session_state.dark_mode)

# ---------------------------------------------------------------------------
# Streamlined 2-Tab Interface
# ---------------------------------------------------------------------------
tab_doc, tab_vision = st.tabs([
    "📄 Document Studio",
    "👁️ Vision Intelligence"
])


# ===========================================================================
# TAB 1: DOCUMENT STUDIO
# ===========================================================================
with tab_doc:
    st.markdown("### Document Ingestion & Executive Synthesis")
    st.caption("Executive document synthesis and natural language contextual querying.")

    doc_upload = st.file_uploader(
        "Upload Corporate Document (PDF, DOCX, TXT)",
        type=["pdf", "docx", "txt", "md"],
        key="doc_uploader"
    )

    if doc_upload:
        try:
            with st.spinner("Parsing document structure, layout, and sections..."):
                doc_data = load_document(doc_upload, doc_upload.name)

            # Translucent Status Badges
            st.markdown(
                f"""
                <div style="display: flex; align-items: center; gap: 8px; margin: 12px 0 16px 0; flex-wrap: wrap;">
                    <span class="status-badge badge-sage">● Ingested & Verified</span>
                    <span class="status-badge badge-neutral"><b>{doc_upload.name}</b></span>
                    <span class="status-badge badge-terracotta">{doc_data['file_type']} Document</span>
                    <span class="status-badge badge-ochre">{doc_data['word_count']:,} Words</span>
                    <span class="status-badge badge-neutral">~{doc_data['reading_time_min']} Min Read</span>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Neural Operations Trigger Area
            st.markdown("#### ⚡ Neural Intelligence Operations")
            action_col1, action_col2, action_col3 = st.columns(3)

            with action_col1:
                btn_exec = st.button("🎯 Executive Brief", use_container_width=True)
            with action_col2:
                btn_notes = st.button("📌 Key Takeaways & Actions", use_container_width=True)
            with action_col3:
                btn_deep = st.button("🔬 Deep-Dive Synthesis", use_container_width=True)

            if btn_exec:
                with st.spinner(f"Synthesizing Executive Brief via {selected_provider}..."):
                    st.session_state.doc_result = generate_document_summary(
                        doc_text=doc_data["full_text"],
                        summary_type="executive",
                        model_provider=selected_provider,
                        model_name=selected_model,
                        api_key=api_key_input,
                        base_url=ollama_base_url
                    )

            if btn_notes:
                with st.spinner(f"Extracting Key Notes & Action Items via {selected_provider}..."):
                    st.session_state.doc_result = generate_document_summary(
                        doc_text=doc_data["full_text"],
                        summary_type="key_takeaways",
                        model_provider=selected_provider,
                        model_name=selected_model,
                        api_key=api_key_input,
                        base_url=ollama_base_url
                    )

            if btn_deep:
                with st.spinner(f"Conducting Deep-Dive Analysis via {selected_provider}..."):
                    st.session_state.doc_result = generate_document_summary(
                        doc_text=doc_data["full_text"],
                        summary_type="deep_dive",
                        model_provider=selected_provider,
                        model_name=selected_model,
                        api_key=api_key_input,
                        base_url=ollama_base_url
                    )

            # Interactive Q&A input
            st.markdown("#### 💬 Ask the Document")
            doc_q_col1, doc_q_col2 = st.columns([4.2, 1.2])
            with doc_q_col1:
                user_question = st.text_input(
                    "Search and query specific facts or numbers in this document:",
                    placeholder="e.g. What were the total research expenditures, operating margins, and cash reserves?",
                    label_visibility="collapsed"
                )
            with doc_q_col2:
                btn_ask = st.button("Query Document", use_container_width=True, type="primary")

            if btn_ask and user_question.strip():
                with st.spinner(f"Searching and reasoning over document context via {selected_provider}..."):
                    st.session_state.doc_result = ask_document_question(
                        doc_text=doc_data["full_text"],
                        question=user_question,
                        model_provider=selected_provider,
                        model_name=selected_model,
                        api_key=api_key_input,
                        base_url=ollama_base_url
                    )

            # --- HERO FOCUS: Stateful Claude Artifacts Workspace ---
            detected_type = doc_data.get("file_type", "Document")
            page_count = doc_data.get("page_count", 1)
            word_count = doc_data.get("word_count", 0)
            detected_entities = [f"{word_count:,} words", f"{page_count} pages", doc_upload.name]

            observations = {
                "Document Type": detected_type,
                "Page Count / Geometry": f"{page_count} Pages ({word_count:,} Words)",
                "Key Entities": detected_entities,
            }

            analysis_text = st.session_state.doc_result if st.session_state.doc_result else doc_data["full_text"]
            has_new_summary = any([btn_exec, btn_notes, btn_deep, (btn_ask and user_question.strip())])
            set_initial_artifact(
                title="Synthesized Document Analysis",
                content=analysis_text,
                observations=observations,
                force_reset=has_new_summary
            )

            render_claude_artifact_workspace(
                router=router,
                preferred_provider=selected_provider,
                key_prefix="doc_artifact"
            )

            # --- DIVIDER & BOTTOM SECTION: Secondary Document Properties ---
            st.markdown("<hr class='enterprise-divider' />", unsafe_allow_html=True)
            with st.expander("📊 Document Properties & Text Inspector", expanded=False if st.session_state.doc_result else True):
                st.markdown(
                    f"""
                    <div class="focus-block" style="padding: 18px 22px; margin: 8px 0 16px 0;">
                        <div class="unified-metrics-grid">
                            <div class="unified-metric-item">
                                <div class="unified-metric-label">Document Format</div>
                                <div class="unified-metric-value" style="color: var(--accent-terracotta);">{doc_data['file_type']}</div>
                            </div>
                            <div class="unified-metric-item">
                                <div class="unified-metric-label">Total Words</div>
                                <div class="unified-metric-value">{doc_data['word_count']:,}</div>
                            </div>
                            <div class="unified-metric-item">
                                <div class="unified-metric-label">Est. Reading Time</div>
                                <div class="unified-metric-value" style="color: var(--accent-sage);">{doc_data['reading_time_min']} <span style="font-size: 0.95rem; font-weight: 500;">min</span></div>
                            </div>
                            <div class="unified-metric-item" style="border-right: none;">
                                <div class="unified-metric-label">Pages / Sections</div>
                                <div class="unified-metric-value" style="color: var(--accent-ochre);">{doc_data['page_count']}</div>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                st.text_area("Extracted Body Text", doc_data["full_text"], height=200, disabled=True)

        except Exception as e:
            st.error(f"Error parsing document: {str(e)}")
    else:
        st.info("💡 Upload a PDF, DOCX, or TXT document above to begin synthesis.")


# ===========================================================================
# TAB 2: VISION INTELLIGENCE
# ===========================================================================
with tab_vision:
    st.markdown("### Computer Vision Inspection & OCR Transcription")
    st.caption("Inspect image geometry, calculate dominant Terracotta/Sage color swatches, and run multimodal visual reasoning.")

    image_upload = st.file_uploader(
        "Upload Visual Asset (PNG, JPG, JPEG, WEBP)",
        type=["png", "jpg", "jpeg", "webp", "bmp", "tiff"],
        key="image_uploader",
        help="Upload infographics, technical charts, scanned receipts, photos, or diagrams."
    )

    if image_upload:
        try:
            pil_img = load_image(image_upload)
            img_meta = extract_image_metadata(pil_img, image_upload.size, image_upload.name)
            swatches = extract_dominant_colors(pil_img, num_colors=5)

            # Translucent Status Badges
            st.markdown(
                f"""
                <div style="display: flex; align-items: center; gap: 8px; margin: 12px 0 16px 0; flex-wrap: wrap;">
                    <span class="status-badge badge-sage">● Asset Ingested</span>
                    <span class="status-badge badge-neutral"><b>{img_meta['filename']}</b></span>
                    <span class="status-badge badge-terracotta">{img_meta['dimensions']}</span>
                    <span class="status-badge badge-ochre">{img_meta['megapixels']} MP</span>
                    <span class="status-badge badge-neutral">{img_meta['format']}</span>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Top Action Area
            vis_col1, vis_col2 = st.columns([1, 1.8])

            with vis_col1:
                st.image(pil_img, caption=img_meta["filename"], use_container_width=True)

            with vis_col2:
                st.markdown("#### ⚡ Multimodal Vision Operations")
                vision_task = st.selectbox(
                    "Select Analysis Task",
                    options=[
                        ("ocr", "🔤 OCR & Text Transcription"),
                        ("describe", "🖼️ Comprehensive Visual Description"),
                        ("chart_diagram", "📈 Chart & Diagram Extraction"),
                        ("document_audit", "📑 Document & Receipt Audit"),
                        ("custom", "❓ Custom Visual Question")
                    ],
                    format_func=lambda x: x[1]
                )

                custom_v_query = ""
                if vision_task[0] == "custom":
                    custom_v_query = st.text_input(
                        "Your question about this image:",
                        placeholder="e.g. Which bar represents the highest quarterly revenue?"
                    )

                btn_run_vision = st.button("🚀 Execute Vision Analysis", use_container_width=True, type="primary")

            if btn_run_vision:
                with st.spinner(f"Analyzing visual content via {selected_provider}..."):
                    st.session_state.vision_result = analyze_image_with_llm(
                        image=pil_img,
                        task_type=vision_task[0],
                        custom_prompt=custom_v_query,
                        model_provider=selected_provider,
                        model_name=selected_model,
                        api_key=api_key_input,
                        base_url=ollama_base_url
                    )

            # --- HERO FOCUS: Stateful Claude Artifacts Workspace ---
            detected_type = img_meta.get("format", "Image")
            width, height = pil_img.size
            detected_entities = [f"{img_meta.get('megapixels')} MP", img_meta.get("mode", "RGB"), image_upload.name]

            observations = {
                "Document Type": detected_type,
                "Page Count / Geometry": f"{width}x{height}",
                "Key Entities": detected_entities,
            }

            analysis_text = st.session_state.vision_result if st.session_state.vision_result else f"### 📷 Visual Asset Ingested: {img_meta['filename']}\n\n- **Geometry & Dimensions**: {width}x{height} pixels\n- **Format**: {img_meta['format']}\n- **Color Mode**: {img_meta['mode']}\n- **Resolution**: {img_meta['megapixels']} MP\n\n*Click 'Execute Vision Analysis' or enter a custom prompt in the Co-Pilot below.*"

            set_initial_artifact(
                title="Synthesized Vision Analysis",
                content=analysis_text,
                observations=observations,
                force_reset=bool(btn_run_vision)
            )

            render_claude_artifact_workspace(
                router=router,
                preferred_provider=selected_provider,
                key_prefix="vision_artifact"
            )

            # --- DIVIDER & BOTTOM SECTION: Secondary Asset Diagnostics ---
            st.markdown("<hr class='enterprise-divider' />", unsafe_allow_html=True)
            render_image_diagnostics_panel(
                img_meta=img_meta,
                swatches=swatches,
                image=pil_img,
                expanded=False if st.session_state.vision_result else True
            )

        except Exception as e:
            st.error(f"Error processing image: {str(e)}")
    else:
        st.info("💡 Upload an image (PNG, JPG, JPEG, WEBP) above to begin visual analysis.")

