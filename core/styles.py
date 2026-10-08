"""core/styles.py

Minimalist Architectural Aesthetic & Executive Porcelain / Dark Glass Design System:
- Full-width, centered executive layout (1220px max-width, no sidebar).
- Dynamic Dark Mode / Light Porcelain theme switching with dynamic color variables.
- Clean CAD/blueprint diagonal grid background with soft ambient occlusion shadows.
- Thin 1px borders with subtle amber top accents (rgba(255, 107, 0, 0.22)).
- Apple SF Pro Display typography and grounded frosted glassmorphic card styling.
"""

from typing import Union
import streamlit as st


def get_google_fonts_css() -> str:
    """Return @import declaration for SF Pro."""
    return """
    @import url('https://fonts.cdnfonts.com/css/sf-pro-display');
    """


def inject_clean_theme(dark_mode: Union[bool, str] = True) -> None:
    """Inject dynamic executive CSS swapping color variables between sleek dark glass
    (#0E1117) and clean executive porcelain (#F8F9FA). Completely hides the sidebar
    and locks a centered, full-width 1220px layout.
    """
    if isinstance(dark_mode, str):
        is_dark = dark_mode.lower() == "dark"
    else:
        is_dark = bool(dark_mode)

    if is_dark:
        bg_primary = "#090A0F"
        bg_card = "rgba(15, 17, 24, 0.72)"
        bg_subtle = "rgba(22, 25, 36, 0.65)"
        text_primary = "#F5F5F7"
        text_secondary = "#94A3B8"
        border_soft = "rgba(255, 255, 255, 0.08)"
        border_top = "rgba(255, 107, 0, 0.22)"
        border_subtle = "rgba(255, 255, 255, 0.05)"
        border_accent = "rgba(255, 122, 0, 0.40)"
        accent_orange = "#FF7A00"
        accent_amber = "#FFAA55"
        shadow_card = "0 4px 20px -2px rgba(0, 0, 0, 0.5), 0 2px 6px -1px rgba(0, 0, 0, 0.4)"
        shadow_hover = "0 8px 28px -4px rgba(0, 0, 0, 0.65), 0 4px 10px -2px rgba(0, 0, 0, 0.5)"
        badge_amber_bg = "rgba(255, 107, 0, 0.15)"
        badge_amber_fg = "#FFAA55"
        badge_amber_border = "rgba(255, 107, 0, 0.22)"
        badge_neutral_bg = "rgba(255, 255, 255, 0.06)"
        badge_neutral_fg = "#94A3B8"
        grid_line = "rgba(255, 255, 255, 0.035)"
        cad_line = "rgba(255, 255, 255, 0.015)"
        brand_title_gradient = "linear-gradient(135deg, #FFFFFF 0%, #FFF0E6 28%, #FFAA55 65%, #FF6B00 100%)"
    else:
        bg_primary = "#F8F9FA"
        bg_card = "rgba(255, 255, 255, 0.88)"
        bg_subtle = "rgba(241, 243, 249, 0.75)"
        text_primary = "#1D1D1F"
        text_secondary = "#6E6E73"
        border_soft = "rgba(0, 0, 0, 0.08)"
        border_top = "rgba(255, 107, 0, 0.22)"
        border_subtle = "rgba(0, 0, 0, 0.04)"
        border_accent = "rgba(255, 122, 0, 0.35)"
        accent_orange = "#FF7A00"
        accent_amber = "#D96B00"
        shadow_card = "0 4px 20px -2px rgba(0, 0, 0, 0.06), 0 2px 6px -1px rgba(0, 0, 0, 0.04)"
        shadow_hover = "0 8px 28px -4px rgba(0, 0, 0, 0.10), 0 4px 10px -2px rgba(0, 0, 0, 0.06)"
        badge_amber_bg = "rgba(255, 107, 0, 0.10)"
        badge_amber_fg = "#D96B00"
        badge_amber_border = "rgba(255, 107, 0, 0.22)"
        badge_neutral_bg = "rgba(0, 0, 0, 0.05)"
        badge_neutral_fg = "#6E6E73"
        grid_line = "rgba(0, 0, 0, 0.035)"
        cad_line = "rgba(0, 0, 0, 0.012)"
        brand_title_gradient = "linear-gradient(135deg, #18191E 0%, #3B4252 28%, #E05300 68%, #FF7A00 100%)"

    font_family = '-apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "SF Pro", "Helvetica Neue", sans-serif'
    fonts_import = get_google_fonts_css()

    css = f"""
    <style>
    {fonts_import}

    :root {{
        --bg-primary: {bg_primary};
        --bg-card: {bg_card};
        --bg-subtle: {bg_subtle};
        --text-color: {text_primary};
        --secondary-text-color: {text_secondary};
        --text-primary: {text_primary};
        --text-secondary: {text_secondary};
        --border-soft: {border_soft};
        --border-top: {border_top};
        --border-subtle: {border_subtle};
        --border-accent: {border_accent};
        --accent-orange: {accent_orange};
        --accent-amber: {accent_amber};
        --shadow-card: {shadow_card};
        --shadow-hover: {shadow_hover};
        --badge-amber-bg: {badge_amber_bg};
        --badge-amber-fg: {badge_amber_fg};
        --badge-amber-border: {badge_amber_border};
        --badge-neutral-bg: {badge_neutral_bg};
        --badge-neutral-fg: {badge_neutral_fg};
        --font-main: {font_family};
    }}

    /* -------------------------------------------------------------
       1. SIDEBAR ELIMINATION & FULL-WIDTH CENTERED LAYOUT
    ------------------------------------------------------------- */
    section[data-testid="stSidebar"],
    div[data-testid="stSidebarCollapseButton"],
    div[data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"],
    [data-testid="stSidebarResizeHandle"] {{
        display: none !important;
        width: 0 !important;
        height: 0 !important;
        visibility: hidden !important;
        pointer-events: none !important;
        margin: 0 !important;
        padding: 0 !important;
    }}

    .main,
    section.main,
    [data-testid="stMain"] {{
        margin-left: 0 !important;
        width: 100% !important;
    }}

    .block-container {{
        max-width: 1220px !important;
        margin: 0 auto !important;
        padding-top: 2.25rem !important;
        padding-bottom: 2.5rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
    }}

    /* Header De-confliction */
    header[data-testid="stHeader"] {{
        height: 0 !important;
        min-height: 0 !important;
        pointer-events: none !important;
        background: transparent !important;
    }}

    /* Hide Unwanted Automated Header Anchors */
    .stMarkdown a.header-anchor,
    a[href^="#"],
    [data-testid="stHeaderActionElements"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"] {{
        display: none !important;
        visibility: hidden !important;
    }}

    /* -------------------------------------------------------------
       TOP-RIGHT DARK MODE TOGGLE (APPLE AMBER ACTIVE FILL)
    ------------------------------------------------------------- */
    div[data-testid="stToggle"] {{
        visibility: visible !important;
        opacity: 1 !important;
        pointer-events: auto !important;
        display: flex !important;
        align-items: center !important;
        justify-content: flex-end !important;
        width: 100% !important;
    }}

    div[data-testid="stToggle"] label {{
        font-family: var(--font-main) !important;
        font-weight: 500 !important;
        font-size: 0.92rem !important;
        color: var(--text-color) !important;
        cursor: pointer !important;
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
    }}

    /* Toggle checkbox track active fill */
    div[data-testid="stToggle"] input:checked ~ div,
    div[data-testid="stToggle"] [aria-checked="true"],
    div[data-testid="stToggle"] div[data-checked="true"] {{
        background-color: #FF6B00 !important;
        border-color: #FF6B00 !important;
    }}

    /* Crisp white circular thumb */
    div[data-testid="stToggle"] [aria-checked="true"] > div,
    div[data-testid="stToggle"] div[data-checked="true"] > div,
    div[data-testid="stToggle"] input:checked ~ div > div {{
        background-color: #FFFFFF !important;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.3) !important;
    }}

    /* -------------------------------------------------------------
       2. CLEAN ARCHITECTURAL CAD / BLUEPRINT GRID BACKGROUND
    ------------------------------------------------------------- */
    html, body, .stApp, [data-testid="stAppViewContainer"] {{
        font-family: var(--font-main) !important;
        background-color: {bg_primary} !important;
        background-image:
            linear-gradient(to right, {grid_line} 1px, transparent 1px),
            linear-gradient(to bottom, {grid_line} 1px, transparent 1px),
            repeating-linear-gradient(-45deg, {cad_line} 0, {cad_line} 1px, transparent 1px, transparent 36px) !important;
        background-size: 36px 36px, 36px 36px, 36px 36px !important;
        background-repeat: repeat, repeat, repeat !important;
        background-attachment: fixed !important;
        color: var(--text-color) !important;
        letter-spacing: -0.018em !important;
        -webkit-font-smoothing: antialiased !important;
        -moz-osx-font-smoothing: grayscale !important;
        text-rendering: optimizeLegibility !important;
    }}

    .stApp {{
        transition: background-color 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    }}

    /* Material Symbols & Icon Ligature Preservation */
    [data-testid="stIconMaterial"],
    .material-symbols-rounded,
    .material-icons,
    span[data-testid="stExpanderToggleIcon"],
    [data-testid="stExpander"] summary svg,
    [data-testid="stExpander"] summary [data-testid="stIconMaterial"] {{
        font-family: 'Material Symbols Rounded', 'Material Icons', sans-serif !important;
        font-style: normal !important;
        letter-spacing: normal !important;
        text-transform: none !important;
        display: inline-block !important;
        white-space: nowrap !important;
        word-wrap: normal !important;
        direction: ltr !important;
        -webkit-font-feature-settings: 'liga' !important;
        font-feature-settings: 'liga' !important;
    }}

    /* Text & Paragraph Typography */
    p, label, td, th, li,
    .stMarkdown, .stMarkdown p, .stMarkdown div, .stMarkdown li,
    div[data-testid="stMarkdownContainer"] p,
    div[data-testid="stMarkdownContainer"] div,
    div[data-testid="stMarkdownContainer"] li,
    div[data-testid="stMarkdownContainer"] td,
    div[data-testid="stMarkdownContainer"] th,
    div[data-testid="stText"],
    .custom-card, .focus-block, .enterprise-card,
    .focus-block p, .enterprise-card p, .custom-card p {{
        color: var(--text-color) !important;
        font-weight: 400 !important;
        line-height: 1.55;
    }}

    /* Headers Typography */
    h1, h2, h3, h4, h5, h6,
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6,
    .focus-block h1, .focus-block h2, .focus-block h3, .focus-block h4,
    .enterprise-card h1, .enterprise-card h2, .enterprise-card h3, .enterprise-card h4 {{
        font-family: var(--font-main) !important;
        color: var(--text-color) !important;
        font-weight: 600 !important;
        letter-spacing: -0.025em !important;
        line-height: 1.25 !important;
    }}

    .stCaption, [data-testid="stCaptionContainer"], p.caption,
    .unified-metric-label, small, .secondary-label {{
        color: var(--secondary-text-color) !important;
        font-weight: 500 !important;
    }}

    /* Brand Accent Typography: Architectural Amber Gradient */
    .brand-title {{
        font-weight: 700;
        background: {brand_title_gradient};
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        display: inline-block;
        letter-spacing: -0.035em;
    }}

    /* -------------------------------------------------------------
       3. ARCHITECTURAL SURFACES & AMBER ACCENTED CARDS
    ------------------------------------------------------------- */
    @keyframes appleFadeInUp {{
        from {{
            opacity: 0;
            transform: perspective(1200px) translateY(10px) scale(0.995);
        }}
        to {{
            opacity: 1;
            transform: perspective(1200px) translateY(0) scale(1.0);
        }}
    }}

    .focus-block, .enterprise-card, .custom-card,
    div[data-testid="stMetric"],
    .stTabs [data-baseweb="tab-panel"],
    section[data-testid="stFileUploadDropzone"],
    div[data-testid="stExpander"],
    .apple-glass-card {{
        animation: appleFadeInUp 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }}

    .focus-block, .enterprise-card, .custom-card, .apple-glass-card {{
        background-color: var(--bg-card) !important;
        backdrop-filter: blur(24px) saturate(190%) !important;
        -webkit-backdrop-filter: blur(24px) saturate(190%) !important;
        border: 1px solid var(--border-soft) !important;
        border-top: 1px solid var(--border-top) !important;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: var(--shadow-card);
        transform: perspective(1200px) translateZ(0);
        transform-style: preserve-3d;
        transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.3s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.25s ease !important;
    }}

    .focus-block:hover, .enterprise-card:hover, .custom-card:hover, .apple-glass-card:hover {{
        transform: perspective(1200px) translateY(-2px) translateZ(4px) !important;
        box-shadow: var(--shadow-hover) !important;
        border-color: var(--border-soft) !important;
        border-top: 1px solid rgba(255, 107, 0, 0.35) !important;
    }}

    /* Unified Metrics Single Wide Focus Block */
    .unified-metrics-grid {{
        display: flex;
        align-items: center;
        justify-content: space-around;
        flex-wrap: wrap;
        gap: 16px;
        padding: 4px 0;
    }}

    .unified-metric-item {{
        flex: 1 1 150px;
        text-align: center;
        padding: 8px 12px;
    }}

    .unified-metric-item:not(:last-child) {{
        border-right: 1px solid var(--border-soft);
    }}

    .unified-metric-label {{
        font-size: 0.74rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.07em;
        color: var(--secondary-text-color) !important;
        margin-bottom: 6px;
    }}

    .unified-metric-value {{
        font-size: 1.85rem;
        font-weight: 700;
        letter-spacing: -0.03em;
        line-height: 1.15;
        color: var(--text-color) !important;
    }}

    /* Native Metric Overrides */
    div[data-testid="stMetric"] {{
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border-soft) !important;
        border-radius: 20px !important;
        padding: 22px 24px !important;
        margin-bottom: 20px !important;
        box-shadow: var(--shadow-card) !important;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }}

    div[data-testid="stMetric"]:hover {{
        transform: translateY(-2px) !important;
        box-shadow: var(--shadow-hover) !important;
        border-color: var(--border-accent) !important;
    }}

    div[data-testid="stMetric"] label {{
        font-size: 0.74rem !important;
        font-weight: 500 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.07em !important;
        color: var(--secondary-text-color) !important;
    }}

    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {{
        font-size: 1.7rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.03em !important;
        color: var(--text-color) !important;
    }}

    /* Delicate Frictionless Dividers */
    .enterprise-divider, .minimal-divider {{
        height: 1px;
        background: linear-gradient(90deg, transparent 0%, var(--border-soft) 25%, var(--border-soft) 75%, transparent 100%);
        margin: 24px 0;
        border: none;
    }}

    /* Status Badges */
    .status-badge,
    .pill-badge,
    .badge-amber,
    .badge-terracotta,
    .badge-sage,
    .badge-ochre,
    .badge-deepseek {{
        display: inline-flex;
        align-items: center;
        gap: 7px;
        padding: 6px 14px;
        border-radius: 9999px;
        font-size: 0.82rem;
        font-weight: 500;
        line-height: 1.4;
        letter-spacing: 0.01em;
        background-color: var(--badge-amber-bg) !important;
        color: var(--badge-amber-fg) !important;
        border: 1px solid var(--badge-amber-border) !important;
        transition: transform 0.16s ease, box-shadow 0.16s ease;
    }}

    .status-badge:hover, .pill-badge:hover {{
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(255, 122, 0, 0.15);
    }}

    .badge-neutral {{
        background-color: var(--badge-neutral-bg) !important;
        color: var(--secondary-text-color) !important;
        border: 1px solid var(--border-soft) !important;
    }}

    /* -------------------------------------------------------------
       4. TABS, BUTTONS & FORM INPUTS
    ------------------------------------------------------------- */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 6px;
        background-color: var(--bg-subtle);
        border-radius: 9999px;
        padding: 5px 6px;
        border: 1px solid var(--border-soft);
        margin-bottom: 24px;
        box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.03);
        display: inline-flex;
        width: auto;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    }}

    .stTabs [data-baseweb="tab-highlight"],
    .stTabs [data-baseweb="tab-border"] {{
        display: none !important;
    }}

    .stTabs [data-baseweb="tab"] {{
        background-color: transparent !important;
        border-radius: 9999px !important;
        color: var(--secondary-text-color) !important;
        font-family: var(--font-main) !important;
        font-weight: 500 !important;
        font-size: 0.92rem !important;
        padding: 9px 22px !important;
        border: none !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }}

    .stTabs [data-baseweb="tab"]:hover {{
        color: var(--text-color) !important;
        background-color: rgba(255, 122, 0, 0.06) !important;
    }}

    .stTabs [aria-selected="true"] {{
        background-color: var(--bg-card) !important;
        color: #FF7A00 !important;
        box-shadow: 0 4px 16px rgba(255, 122, 0, 0.16), 0 2px 6px rgba(0, 0, 0, 0.04) !important;
        border: 1px solid rgba(255, 122, 0, 0.4) !important;
    }}

    .stTabs [aria-selected="true"] p {{
        font-weight: 600 !important;
        color: #FF7A00 !important;
    }}

    /* Primary CTA Buttons: Clean Amber Action */
    .stButton > button,
    button[kind="primary"] {{
        background: linear-gradient(135deg, #FF7A00 0%, #E05300 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 9999px !important;
        padding: 0.62rem 1.6rem !important;
        font-weight: 500 !important;
        font-size: 0.92rem !important;
        font-family: var(--font-main) !important;
        letter-spacing: -0.01em !important;
        transition: all 0.18s cubic-bezier(0.16, 1, 0.3, 1) !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25) !important;
    }}

    .stButton > button:hover,
    button[kind="primary"]:hover {{
        background: linear-gradient(135deg, #FF8C1A 0%, #EA5C00 100%) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.35) !important;
    }}

    .stButton > button:active,
    button[kind="primary"]:active {{
        transform: scale(0.97) !important;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.2) !important;
    }}

    /* Download Button: Clean Amber Translucent Outline */
    .stDownloadButton > button {{
        background: transparent !important;
        color: #FF7A00 !important;
        border: 1px solid rgba(255, 122, 0, 0.4) !important;
        border-radius: 9999px !important;
        padding: 0.55rem 1.4rem !important;
        font-weight: 500 !important;
        font-size: 0.88rem !important;
        font-family: var(--font-main) !important;
        transition: all 0.18s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }}

    .stDownloadButton > button:hover {{
        background: rgba(255, 122, 0, 0.10) !important;
        border-color: #FF7A00 !important;
        transform: translateY(-1px) !important;
    }}

    /* Form Fields & Text Inputs */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {{
        background-color: var(--bg-card) !important;
        color: var(--text-color) !important;
        border: 1px solid var(--border-soft) !important;
        border-radius: 16px !important;
        padding: 12px 18px !important;
        font-family: var(--font-main) !important;
        font-weight: 400 !important;
        font-size: 0.94rem !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02) !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
    }}

    .stTextInput input:focus,
    .stSelectbox div[data-baseweb="select"]:focus-within {{
        border-color: #FF6B00 !important;
        box-shadow: 0 0 0 3px rgba(255, 107, 0, 0.18) !important;
    }}

    /* Text Areas */
    .stTextArea textarea {{
        background-color: var(--bg-card) !important;
        color: var(--text-color) !important;
        border: 1px solid var(--border-soft) !important;
        border-radius: 18px !important;
        padding: 16px 20px !important;
        font-family: var(--font-main) !important;
        font-weight: 400 !important;
        font-size: 0.95rem !important;
        line-height: 1.6 !important;
        min-height: 120px !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02) !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
    }}

    .stTextArea textarea:focus {{
        border-color: #FF6B00 !important;
        box-shadow: 0 0 0 3px rgba(255, 107, 0, 0.18) !important;
    }}

    /* File Uploader Dropzone: Grounded Frosted Dark Glass with Thin 1px Border & Amber Top Accent */
    section[data-testid="stFileUploadDropzone"] {{
        background-color: var(--bg-card) !important;
        backdrop-filter: blur(24px) saturate(190%) !important;
        -webkit-backdrop-filter: blur(24px) saturate(190%) !important;
        border: 1px dashed var(--border-soft) !important;
        border-top: 1px solid var(--border-top) !important;
        border-radius: 16px !important;
        padding: 28px !important;
        margin-bottom: 20px !important;
        box-shadow: var(--shadow-card) !important;
        transition: border-color 0.2s ease, background-color 0.2s ease, box-shadow 0.2s ease !important;
    }}

    section[data-testid="stFileUploadDropzone"]:hover {{
        border-color: rgba(255, 107, 0, 0.4) !important;
        border-top: 1px solid rgba(255, 107, 0, 0.35) !important;
        background-color: rgba(255, 122, 0, 0.03) !important;
        box-shadow: var(--shadow-hover) !important;
    }}

    /* Rounded Expanders: Grounded Glassmorphic Finish with Thin 1px Border & Amber Top Accent */
    div[data-testid="stExpander"] {{
        background-color: var(--bg-card) !important;
        backdrop-filter: blur(24px) saturate(190%) !important;
        -webkit-backdrop-filter: blur(24px) saturate(190%) !important;
        border: 1px solid var(--border-soft) !important;
        border-top: 1px solid var(--border-top) !important;
        border-radius: 16px !important;
        box-shadow: var(--shadow-card) !important;
        overflow: hidden !important;
        margin-bottom: 20px !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
    }}

    div[data-testid="stExpander"] details summary {{
        padding: 14px 20px !important;
        border-radius: 20px !important;
        color: var(--text-color) !important;
        cursor: pointer !important;
    }}

    div[data-testid="stExpander"] details summary:hover {{
        background-color: rgba(255, 122, 0, 0.04) !important;
    }}

    div[data-testid="stExpander"] details summary p {{
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        margin: 0 !important;
    }}

    div[data-testid="stExpander"] div[data-testid="stExpanderDetails"] {{
        padding: 6px 20px 20px 20px !important;
        border-top: 1px solid var(--border-soft) !important;
    }}

    /* Swatch Box */
    .swatch-box {{
        display: flex;
        align-items: center;
        border-radius: 14px;
        padding: 10px 16px;
        margin-bottom: 8px;
        font-weight: 500;
        font-size: 0.88rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        border: 1px solid rgba(0, 0, 0, 0.06);
        transition: transform 0.16s ease, box-shadow 0.16s ease;
    }}

    .swatch-box:hover {{
        transform: translateX(4px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.09);
    }}

    /* Markdown Artifact Tables & Structured Data */
    .stMarkdown table, .focus-block table {{
        width: 100% !important;
        border-collapse: collapse !important;
        margin: 16px 0 !important;
        font-size: 0.92rem !important;
        border-radius: 12px !important;
        overflow: hidden !important;
    }}

    .stMarkdown th, .focus-block th {{
        background-color: var(--bg-subtle) !important;
        color: var(--text-color) !important;
        font-weight: 600 !important;
        border-bottom: 2px solid var(--border-soft) !important;
        padding: 11px 16px !important;
        text-align: left !important;
    }}

    .stMarkdown td, .focus-block td {{
        border-bottom: 1px solid var(--border-soft) !important;
        padding: 10px 16px !important;
        color: var(--text-color) !important;
    }}

    .stMarkdown tr:hover td, .focus-block tr:hover td {{
        background-color: rgba(255, 122, 0, 0.04) !important;
    }}

    /* -------------------------------------------------------------
       5. VISUAL DIFF INSPECTOR COMPONENT
    ------------------------------------------------------------- */
    .diff-inspector-container {{
        max-height: 520px !important;
        overflow-y: auto !important;
        overflow-x: auto !important;
        padding: 18px 20px !important;
        border-radius: 16px !important;
        background: rgba(18, 20, 26, 0.85) !important;
        backdrop-filter: blur(20px) saturate(190%) !important;
        border: 1px solid var(--border-soft) !important;
        border-top: 1px solid var(--border-top) !important;
        box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.4), 0 4px 16px rgba(0, 0, 0, 0.25) !important;
        margin: 10px 0 20px 0 !important;
    }}

    .diff-line {{
        font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Monaco, Consolas, monospace !important;
        line-height: 1.55 !important;
        font-size: 0.86rem !important;
    }}

    .diff-chunk {{
        color: #FFAA55 !important;
        background: rgba(255, 140, 40, 0.15) !important;
        border-radius: 6px !important;
        padding: 4px 10px !important;
        margin: 6px 0 3px 0 !important;
        font-weight: 600 !important;
        display: inline-block !important;
    }}

    .diff-add {{
        color: #30D158 !important;
        background: rgba(48, 209, 88, 0.15) !important;
        border-left: 3px solid #30D158 !important;
        padding: 3px 10px !important;
        margin: 1px 0 !important;
        border-radius: 0 4px 4px 0 !important;
        white-space: pre-wrap !important;
        word-break: break-word !important;
    }}

    .diff-del {{
        color: #FF453A !important;
        background: rgba(255, 69, 58, 0.15) !important;
        border-left: 3px solid #FF453A !important;
        text-decoration: line-through !important;
        padding: 3px 10px !important;
        margin: 1px 0 !important;
        border-radius: 0 4px 4px 0 !important;
        white-space: pre-wrap !important;
        word-break: break-word !important;
    }}

    .diff-same {{
        color: #A1A1A6 !important;
        padding: 2px 10px !important;
        margin: 1px 0 !important;
        white-space: pre-wrap !important;
        word-break: break-word !important;
    }}

    .diff-meta {{
        color: #8E8E93 !important;
        padding: 2px 8px !important;
        margin: 1px 0 !important;
        font-size: 0.80rem !important;
        font-weight: 500 !important;
    }}

    /* Minimalist Fluid Scrollbars */
    ::-webkit-scrollbar {{
        width: 6px;
        height: 6px;
    }}
    ::-webkit-scrollbar-track {{
        background: transparent;
    }}
    ::-webkit-scrollbar-thumb {{
        background: rgba(110, 110, 115, 0.25);
        border-radius: 9999px;
    }}
    ::-webkit-scrollbar-thumb:hover {{
        background: #FF7A00;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def apply_custom_theme(theme_mode: str = "Light") -> None:
    """Backward-compatible wrapper for inject_clean_theme."""
    is_dark = theme_mode.lower() == "dark" if isinstance(theme_mode, str) else bool(theme_mode)
    inject_clean_theme(dark_mode=is_dark)


def render_interactive_3d_background() -> None:
    """Legacy stub. 3D canvas replaced with subtle, high-performance executive CSS radial gradients.
    Cleans up any legacy canvas elements from DOM.
    """
    import streamlit.components.v1 as components

    cleanup_js = """
    <script>
    (function cleanupOldCanvas() {
        try {
            const topDoc = (window.parent && window.parent.document) ? window.parent.document : document;
            ['ambient-3d-canvas', 'ambient-3d-node-mesh'].forEach(id => {
                const el = topDoc.getElementById(id);
                if (el && el.parentNode) {
                    el.parentNode.removeChild(el);
                }
            });
        } catch (e) {}
    })();
    </script>
    """
    components.html(cleanup_js, height=0, width=0)
