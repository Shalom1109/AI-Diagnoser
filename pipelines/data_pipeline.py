"""pipelines/data_pipeline.py

Structured data processing, statistical profiling, and interactive visualization suite.
Features:
1. Secure ingestion for CSV and Excel (.xlsx, .xls) files into Pandas DataFrames.
2. Comprehensive Data Health Card (rows, columns, missing data, memory, duplicates, column diagnostics).
3. Interactive Plotly charts styled specifically with Terracotta (#C65D3B) and Sage (#87A878) color tokens.
4. AI-assisted dataset insight generator connecting to `core.llm_router.query_llm`.
"""

import io
import os
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from core.llm_router import query_llm

# ---------------------------------------------------------------------------
# Terracotta & Sage Design System Color Tokens for Plotly
# ---------------------------------------------------------------------------
TERRACOTTA = "#C65D3B"
SAGE = "#87A878"
OCHRE = "#D4A574"
WARM_CREAM = "#F5F1E8"
CHARCOAL = "#2D2D2D"
DEEP_SAGE = "#5C7652"
DEEP_TERRACOTTA = "#9C4226"

DISCRETE_PALETTE = [TERRACOTTA, SAGE, OCHRE, DEEP_SAGE, DEEP_TERRACOTTA, "#8C7B6B", "#B57C48"]

# Diverging / Sequential continuous color scale for heatmaps and metric gradients
TERRACOTTA_SAGE_CONTINUOUS = [
    [0.0, SAGE],
    [0.5, WARM_CREAM],
    [1.0, TERRACOTTA]
]


def _apply_theme_to_figure(fig: go.Figure, dark_mode: bool = False, title: Optional[str] = None) -> go.Figure:
    """Apply consistent Terracotta/Sage typography, margins, and borders to any Plotly figure."""
    bg_color = "#262626" if dark_mode else "#FFFFFF"
    text_color = "#F5F1E8" if dark_mode else "#2D2D2D"
    grid_color = "rgba(255, 255, 255, 0.08)" if dark_mode else "rgba(45, 45, 45, 0.08)"
    border_color = "#383838" if dark_mode else "#E3DCD1"

    fig.update_layout(
        title=dict(
            text=title or "",
            font=dict(size=16, color=text_color, family="Space Grotesk, sans-serif"),
            x=0.02,
            y=0.96
        ) if title else None,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=bg_color,
        font=dict(color=text_color, family="Space Grotesk, sans-serif", size=12),
        margin=dict(l=40, r=40, t=50 if title else 25, b=40),
        xaxis=dict(
            gridcolor=grid_color,
            zerolinecolor=grid_color,
            tickfont=dict(color=text_color)
        ),
        yaxis=dict(
            gridcolor=grid_color,
            zerolinecolor=grid_color,
            tickfont=dict(color=text_color)
        ),
        legend=dict(
            font=dict(color=text_color),
            bgcolor="rgba(0,0,0,0)",
            bordercolor=border_color,
            borderwidth=1
        ),
        hoverlabel=dict(
            bgcolor=bg_color,
            font_size=12,
            font_family="Space Grotesk, sans-serif",
            bordercolor=TERRACOTTA
        )
    )
    return fig


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


# ---------------------------------------------------------------------------
# 1. Secure Data Loading
# ---------------------------------------------------------------------------
def load_structured_data(file_source: Any, filename: str) -> pd.DataFrame:
    """Safely parse CSV or Excel data into a Pandas DataFrame with error resilience."""
    ext = os.path.splitext(filename)[1].lower()
    file_bytes = resolve_file_bytes(file_source)
    buffer = io.BytesIO(file_bytes)

    if ext in (".xlsx", ".xls"):
        # Excel files parsed using openpyxl engine
        df = pd.read_excel(buffer, engine="openpyxl")
    elif ext == ".csv":
        # Attempt comma, semicolon, tab with encoding fallback
        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
        loaded = False
        last_err = None
        for enc in encodings:
            buffer.seek(0)
            try:
                # Use C engine with auto-detection of common separators
                df = pd.read_csv(buffer, encoding=enc, sep=None, engine="python")
                loaded = True
                break
            except Exception as e:
                last_err = e
                continue
        if not loaded:
            buffer.seek(0)
            df = pd.read_csv(buffer, encoding="utf-8", on_bad_lines="skip")
    else:
        # Fallback to CSV parser
        buffer.seek(0)
        df = pd.read_csv(buffer)

    # Sanitize column names (strip whitespace)
    df.columns = [str(c).strip() for c in df.columns]
    return df


# ---------------------------------------------------------------------------
# 2. Comprehensive Data Health Card
# ---------------------------------------------------------------------------
def generate_data_health_card(df: pd.DataFrame, filename: str = "Dataset") -> Dict[str, Any]:
    """Compute detailed health metrics, missingness, memory usage, and data types."""
    total_rows, total_cols = df.shape
    total_cells = total_rows * total_cols
    missing_cells = int(df.isna().sum().sum())
    missing_pct = round((missing_cells / max(total_cells, 1)) * 100, 2)

    duplicate_rows = int(df.duplicated().sum())
    duplicate_pct = round((duplicate_rows / max(total_rows, 1)) * 100, 2)

    memory_bytes = int(df.memory_usage(deep=True).sum())
    if memory_bytes < 1024 * 1024:
        memory_str = f"{memory_bytes / 1024:.1f} KB"
    else:
        memory_str = f"{memory_bytes / (1024 * 1024):.2f} MB"

    # Identify column dtypes
    numeric_cols = list(df.select_dtypes(include=[np.number]).columns)
    datetime_cols = list(df.select_dtypes(include=["datetime", "datetimetz"]).columns)
    categorical_cols = [c for c in df.columns if c not in numeric_cols and c not in datetime_cols]

    # Column-level diagnostics
    col_details = []
    for col in df.columns:
        col_series = df[col]
        n_missing = int(col_series.isna().sum())
        missing_rate = round((n_missing / max(total_rows, 1)) * 100, 1)
        n_unique = int(col_series.nunique(dropna=True))
        dtype_str = str(col_series.dtype)

        # Sample value representation
        sample_vals = col_series.dropna().head(3).tolist()
        sample_str = ", ".join([str(v) for v in sample_vals]) if sample_vals else "Empty"

        col_details.append({
            "Column": col,
            "Type": dtype_str,
            "Missing": f"{n_missing} ({missing_rate}%)",
            "Unique": n_unique,
            "Sample": sample_str
        })

    return {
        "filename": filename,
        "total_rows": total_rows,
        "total_cols": total_cols,
        "total_cells": total_cells,
        "missing_cells": missing_cells,
        "missing_percentage": missing_pct,
        "duplicate_rows": duplicate_rows,
        "duplicate_percentage": duplicate_pct,
        "memory_usage": memory_str,
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols,
        "datetime_columns": datetime_cols,
        "columns_summary_df": pd.DataFrame(col_details)
    }


# ---------------------------------------------------------------------------
# 3. Interactive Plotly Charts in Terracotta & Sage
# ---------------------------------------------------------------------------
def create_correlation_heatmap(df: pd.DataFrame, dark_mode: bool = False) -> Optional[go.Figure]:
    """Generate an annotated correlation heatmap for numeric features."""
    num_df = df.select_dtypes(include=[np.number])
    if num_df.shape[1] < 2:
        return None

    corr = num_df.corr().round(2)

    fig = go.Figure(data=go.Heatmap(
        z=corr.values,
        x=corr.columns.tolist(),
        y=corr.index.tolist(),
        colorscale=TERRACOTTA_SAGE_CONTINUOUS,
        zmin=-1.0,
        zmax=1.0,
        colorbar=dict(
            title=dict(text="Correlation", side="right"),
            tickfont=dict(color="#F5F1E8" if dark_mode else "#2D2D2D")
        ),
        text=corr.values,
        texttemplate="%{text}",
        textfont={"size": 11, "color": "#2D2D2D"},
        hoverongaps=False
    ))

    fig = _apply_theme_to_figure(
        fig,
        dark_mode=dark_mode,
        title="Pearson Correlation Matrix (Terracotta & Sage)"
    )
    return fig


def create_distribution_plot(
    df: pd.DataFrame,
    column_name: str,
    chart_type: str = "histogram",
    dark_mode: bool = False
) -> go.Figure:
    """Generate distribution histogram or box plot for a specified numeric column."""
    series = df[column_name].dropna()

    if chart_type.lower() == "box":
        fig = go.Figure()
        fig.add_trace(go.Box(
            y=series,
            name=column_name,
            marker_color=TERRACOTTA,
            boxpoints="outliers",
            line=dict(color=DEEP_TERRACOTTA, width=1.5),
            fillcolor="rgba(198, 93, 59, 0.45)"
        ))
        title = f"Box Plot Distribution: {column_name}"
    else:
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=series,
            name=column_name,
            marker=dict(
                color=TERRACOTTA,
                line=dict(color=WARM_CREAM if dark_mode else "#FFFFFF", width=1)
            ),
            opacity=0.85
        ))
        title = f"Frequency Histogram: {column_name}"

    return _apply_theme_to_figure(fig, dark_mode=dark_mode, title=title)


def create_scatter_plot(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    color_col: Optional[str] = None,
    dark_mode: bool = False
) -> go.Figure:
    """Generate an interactive scatter plot with optional categorical/numerical coloring."""
    if color_col and color_col in df.columns:
        fig = px.scatter(
            df,
            x=x_col,
            y=y_col,
            color=color_col,
            color_discrete_sequence=DISCRETE_PALETTE,
            opacity=0.85
        )
    else:
        fig = px.scatter(
            df,
            x=x_col,
            y=y_col,
            opacity=0.85
        )
        fig.update_traces(marker=dict(color=TERRACOTTA, size=8, line=dict(width=1, color=WARM_CREAM)))

    title = f"Scatter Analysis: {x_col} vs {y_col}"
    return _apply_theme_to_figure(fig, dark_mode=dark_mode, title=title)


def create_bar_plot(
    df: pd.DataFrame,
    x_col: str,
    y_col: Optional[str] = None,
    aggregation: str = "count",
    dark_mode: bool = False
) -> go.Figure:
    """Generate an aggregated or count bar chart using Sage and Terracotta accents."""
    if y_col and y_col in df.columns and aggregation != "count":
        # Groupby aggregation
        if aggregation == "mean":
            agg_df = df.groupby(x_col)[y_col].mean().reset_index()
            title = f"Mean {y_col} by {x_col}"
        elif aggregation == "sum":
            agg_df = df.groupby(x_col)[y_col].sum().reset_index()
            title = f"Total {y_col} by {x_col}"
        else:
            agg_df = df.groupby(x_col)[y_col].median().reset_index()
            title = f"Median {y_col} by {x_col}"

        # Top 20 categories for visual clarity
        agg_df = agg_df.sort_values(by=y_col, ascending=False).head(20)

        fig = px.bar(
            agg_df,
            x=x_col,
            y=y_col,
            color_discrete_sequence=[SAGE]
        )
    else:
        # Simple frequency counts
        counts = df[x_col].value_counts().head(20).reset_index()
        counts.columns = [x_col, "Count"]
        title = f"Value Distribution of {x_col}"

        fig = px.bar(
            counts,
            x=x_col,
            y="Count",
            color_discrete_sequence=[SAGE]
        )

    fig.update_traces(marker_line_color=DEEP_SAGE, marker_line_width=1.2, opacity=0.9)
    return _apply_theme_to_figure(fig, dark_mode=dark_mode, title=title)


def create_line_plot(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    color_col: Optional[str] = None,
    dark_mode: bool = False
) -> go.Figure:
    """Generate a time series or trend line plot."""
    sorted_df = df.sort_values(by=x_col)

    if color_col and color_col in df.columns:
        fig = px.line(
            sorted_df,
            x=x_col,
            y=y_col,
            color=color_col,
            color_discrete_sequence=DISCRETE_PALETTE
        )
    else:
        fig = px.line(
            sorted_df,
            x=x_col,
            y=y_col,
            color_discrete_sequence=[TERRACOTTA]
        )
        fig.update_traces(line=dict(width=2.5))

    title = f"Trend Analysis: {y_col} over {x_col}"
    return _apply_theme_to_figure(fig, dark_mode=dark_mode, title=title)


# ---------------------------------------------------------------------------
# 4. LLM Dataset Intelligence & Natural Language Insights
# ---------------------------------------------------------------------------
def generate_data_insights(
    df: pd.DataFrame,
    user_query: Optional[str] = None,
    model_provider: str = "Google Gemini",
    model_name: str = "gemini-3.8-flash",
    api_key: Optional[str] = None,
    **kwargs
) -> str:
    """Generate statistical observations, anomaly detections, or answer user data queries."""
    health = generate_data_health_card(df)

    # Prepare statistical summary of dataset for the prompt
    num_summary = ""
    num_df = df.select_dtypes(include=[np.number])
    if not num_df.empty:
        desc = num_df.describe().round(2).to_string()
        num_summary = f"\nNumerical Summary Statistics:\n{desc}\n"

    # Top correlations
    corr_summary = ""
    if num_df.shape[1] >= 2:
        c = num_df.corr().unstack().sort_values(ascending=False)
        # Filter self correlations
        c = c[c < 0.999].head(8)
        if not c.empty:
            corr_summary = f"\nStrongest Positive Correlations:\n{c.to_string()}\n"

    base_context = (
        f"Dataset Overview:\n"
        f"- Rows: {health['total_rows']}, Columns: {health['total_cols']}\n"
        f"- Missing Values: {health['missing_cells']} ({health['missing_percentage']}% of cells)\n"
        f"- Duplicate Rows: {health['duplicate_rows']}\n"
        f"- Column Types: Numeric ({len(health['numeric_columns'])}), Categorical ({len(health['categorical_columns'])})\n"
        f"{num_summary}"
        f"{corr_summary}"
    )

    if user_query and user_query.strip():
        prompt = (
            f"You are an expert data scientist and quantitative analyst. "
            f"Answer the following user query based on the dataset summary provided below.\n\n"
            f"{base_context}\n\n"
            f"User Query: {user_query.strip()}"
        )
    else:
        prompt = (
            f"You are an expert data scientist and quantitative analyst. "
            f"Conduct an automated Exploratory Data Analysis (EDA) on the dataset summary provided below. "
            f"Format your response in Markdown with:\n"
            f"### 📈 Key Statistical Patterns & Distributions\n"
            f"### ⚠️ Data Quality & Missingness Observations\n"
            f"### 💡 Strategic Takeaways & Predictive Hypotheses\n\n"
            f"{base_context}"
        )

    return query_llm(
        prompt=prompt,
        model_provider=model_provider,
        model_name=model_name,
        api_key=api_key,
        **kwargs
    )
