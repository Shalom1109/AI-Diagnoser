# Multimodal Document Intelligence Studio

A production-ready Python Streamlit application for multimodal document analysis, computer vision OCR, and structured tabular diagnostics. Built with a bespoke **Terracotta (#C65D3B)** and **Sage (#87A878)** design system, dynamic Google Fonts switching, seamless Dark/Light themes, and **Zero-Cost Model Routing**.

---

## 🌟 Key Architecture & Capabilities

### 1. Document Intelligence (`pipelines/document_pipeline.py`)
- Ingests **PDF** (via `pypdf`), Microsoft Word **DOCX** (via `python-docx`), and **TXT/Markdown**.
- Technical Metrics: Word count, page/paragraph breakdown, estimated reading time.
- Operations: **Executive Brief**, **Key Takeaways & Action Items**, **Deep-Dive Synthesis**.
- **Ask the Document**: Contextual semantic Q&A with evidence retrieval and citation ranking.
- **Export**: One-click download of synthesized analysis as formatted Markdown reports.

### 2. Vision & Image Studio (`pipelines/image_pipeline.py`)
- Ingests **PNG**, **JPG**, **JPEG**, **WEBP**, **BMP**, and **TIFF** via Pillow with EXIF auto-orientation.
- Technical Metadata: Resolution, Megapixels, Aspect Ratio, Color Space, File Size, DPI, and sanitized EXIF.
- **Dominant Color Swatches**: Quantization engine extracting top 5 dominant colors with hex codes, RGB tuples, coverage percentages, and text contrast badges.
- Multimodal Operations: High-accuracy OCR transcription, visual description, document & receipt audits, and chart/diagram extraction.

### 3. Structured Data Analytics (`pipelines/data_pipeline.py`)
- Ingests **CSV**, **XLSX**, and **XLS** datasets via Pandas and Openpyxl.
- **Comprehensive Data Health Card**: Rows, columns, missing cell percentage, duplicate count, memory footprint, and column-level type diagnostics.
- **Interactive Plotly Visualizations**:
  - Pearson Correlation Matrix Heatmap (styled with continuous Sage to Terracotta ramp).
  - Frequency Histograms & Box Plots.
  - Multi-feature Scatter Relationships with optional categorical colors.
  - Categorical Bar Charts (Counts or Mean/Sum aggregations).
  - Time Trend Line Charts.
- **AI Dataset Intelligence**: Automated Exploratory Data Analysis (EDA) and natural language queries over tabular datasets.

### 4. Zero-Cost Model Routing (`core/llm_router.py`)
- **Google Gemini (Free Tier)**: Multimodal text & vision queries via `gemini-3.8-flash` or `gemini-3.1-pro-preview` with smart rate-limit cascade.
- **Groq Cloud (Free Tier)**: Sub-second inference via `llama-3.3-70b-versatile` and `llama-3.2-11b-vision-preview`.
- **Ollama (Local Private)**: Connects to local endpoints (`http://localhost:11434`) for offline execution.
- **Offline Heuristics (Zero-Config)**: 100% pure Python TF-IDF sentence salience, semantic overlap search, and image visual profiler. Runs with zero external models or internet connection.

---

## 🚀 Quickstart

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Streamlit Application
```bash
streamlit run main.py
```

The application will launch in your browser at `http://localhost:8501`.

---

## 🎨 Theme & Typography Controls
Use the sidebar controls to:
- Switch between **Light Mode** (warm cream `#F5F1E8`) and **Dark Mode** (charcoal `#1A1A1A`).
- Dynamically toggle typography presets:
  - `Space Grotesk` (Modern geometric)
  - `Playfair Display` (High-end editorial)
  - `JetBrains Mono` (Technical monospace)
  - `Plus Jakarta Sans` (Clean corporate humanist)
- Test immediately using the **Instant Demo Datasets** radio button in the sidebar.
