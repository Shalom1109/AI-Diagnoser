"""core/ui_components.py

Streamlit encapsulated UI components and telemetry widgets.
Provides dark-mode compatible telemetry rendering with latency color coding,
active provider tracking, failover status badges, and Admin Observability Dashboards.
"""

import difflib
import html
import io
import json
import os
import re
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from core.llm_router import get_last_telemetry
from core.telemetry import get_recent_events


def get_latency_color(latency_ms: float) -> str:
    """Return CSS color variable or hex based on latency thresholds:
    <800ms green (#10B981)
    800-2500ms yellow (#F59E0B)
    >2500ms orange/red (#EF4444)
    """
    if latency_ms < 800.0:
        return "#10B981"  # Vibrant Emerald Green
    elif latency_ms <= 2500.0:
        return "#F59E0B"  # Amber / Warm Yellow
    else:
        return "#EF4444"  # Vivid Red / Coral Orange


def render_3d_hero_monolith(height: int = 190) -> None:
    """Renders an interactive, physical glass prism hero monolith powered by WebGL and Three.js:
    - Outer physical glass prism (MeshPhysicalMaterial with transmission, refraction, and clearcoat).
    - Inner glowing amber intelligence octahedron that floats, pulses, and rotates.
    - Central warm point light that dynamically illuminates internal glass facets.
    - Smooth mouse parallax camera tilt bound to cursor movement.
    - Seamless transparent canvas integrating with the aurora obsidian background.
    """
    import streamlit.components.v1 as components

    monolith_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            html, body {{
                margin: 0;
                padding: 0;
                overflow: hidden;
                width: 100%;
                height: 100%;
                background: transparent;
            }}
            #canvas-wrapper {{
                width: 100%;
                height: {height}px;
                position: relative;
                display: flex;
                justify-content: center;
                align-items: center;
            }}
            canvas {{
                display: block;
                width: 100%;
                height: 100%;
                outline: none;
            }}
        </style>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    </head>
    <body>
        <div id="canvas-wrapper">
            <canvas id="monolith-canvas"></canvas>
        </div>
        <script>
        (function() {{
            function init() {{
                const canvas = document.getElementById('monolith-canvas');
                const wrapper = document.getElementById('canvas-wrapper');
                if (!canvas || !wrapper || typeof THREE === 'undefined') return;

                const width = wrapper.clientWidth || 800;
                const height = wrapper.clientHeight || {height};

                // Scene & Perspective Camera
                const scene = new THREE.Scene();
                const camera = new THREE.PerspectiveCamera(38, width / height, 0.1, 100);
                camera.position.set(0, 0.15, 5.0);

                // WebGL Renderer with High Performance & Tone Mapping
                const renderer = new THREE.WebGLRenderer({{
                    canvas: canvas,
                    alpha: true,
                    antialias: true,
                    powerPreference: "high-performance"
                }});
                renderer.setSize(width, height);
                renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
                renderer.toneMapping = THREE.ACESFilmicToneMapping;
                renderer.toneMappingExposure = 1.15;

                // Central Interactive Monolith Group
                const group = new THREE.Group();
                scene.add(group);

                // 1. Outer Physical Glass Prism (Tapered Hexagonal Monolith)
                const prismGeo = new THREE.CylinderGeometry(0.88, 1.12, 2.4, 6);
                const glassMat = new THREE.MeshPhysicalMaterial({{
                    color: 0xffffff,
                    transmission: 0.94,
                    opacity: 1.0,
                    transparent: true,
                    roughness: 0.08,
                    metalness: 0.05,
                    ior: 1.52,
                    thickness: 1.4,
                    specularIntensity: 1.0,
                    specularColor: 0xffeedd,
                    clearcoat: 1.0,
                    clearcoatRoughness: 0.06,
                    depthWrite: false
                }});
                const prismMesh = new THREE.Mesh(prismGeo, glassMat);
                group.add(prismMesh);

                // Specular Edge Lines for Apple Chamfered Highlights
                const edgesGeo = new THREE.EdgesGeometry(prismGeo);
                const edgeMat = new THREE.LineBasicMaterial({{
                    color: 0xffaa55,
                    transparent: true,
                    opacity: 0.45
                }});
                const edges = new THREE.LineSegments(edgesGeo, edgeMat);
                group.add(edges);

                // 2. Inner Glowing Amber Intelligence Core (Octahedron)
                const octaGeo = new THREE.OctahedronGeometry(0.5, 0);
                const octaMat = new THREE.MeshStandardMaterial({{
                    color: 0xff7a00,
                    emissive: 0xff5500,
                    emissiveIntensity: 0.95,
                    roughness: 0.22,
                    metalness: 0.28
                }});
                const octahedron = new THREE.Mesh(octaGeo, octaMat);
                group.add(octahedron);

                // Inner Geometric Wireframe Lattice
                const wireGeo = new THREE.WireframeGeometry(octaGeo);
                const wireMat = new THREE.LineBasicMaterial({{
                    color: 0xffe0b2,
                    transparent: true,
                    opacity: 0.75
                }});
                const wireMesh = new THREE.LineSegments(wireGeo, wireMat);
                octahedron.add(wireMesh);

                // 3. Central Dynamic Amber Point Light (Illuminates Inner Facets)
                const coreLight = new THREE.PointLight(0xff7a00, 3.2, 8);
                coreLight.position.set(0, 0, 0);
                group.add(coreLight);

                // 4. Subtle Orbital Halo Ring
                const ringGeo = new THREE.TorusGeometry(1.6, 0.016, 16, 72);
                const ringMat = new THREE.MeshBasicMaterial({{
                    color: 0xff9922,
                    transparent: true,
                    opacity: 0.35
                }});
                const ring = new THREE.Mesh(ringGeo, ringMat);
                ring.rotation.x = Math.PI / 2.7;
                group.add(ring);

                // 5. Environmental Lights
                const ambient = new THREE.AmbientLight(0xfff8ee, 0.85);
                scene.add(ambient);

                const topDir = new THREE.DirectionalLight(0xffeedd, 2.2);
                topDir.position.set(4, 7, 5);
                scene.add(topDir);

                const rimDir = new THREE.DirectionalLight(0xff7a00, 1.8);
                rimDir.position.set(-5, -3, 3);
                scene.add(rimDir);

                // 6. Smooth Mouse Parallax
                let targetRotX = 0;
                let targetRotY = 0;
                const topWin = (window.parent && window.parent.window) ? window.parent.window : window;

                function onPointerMove(e) {{
                    const cx = topWin.innerWidth ? topWin.innerWidth / 2 : 500;
                    const cy = topWin.innerHeight ? topWin.innerHeight / 2 : 400;
                    const normX = (e.clientX - cx) / cx;
                    const normY = (e.clientY - cy) / cy;
                    targetRotY = normX * 0.75;
                    targetRotX = normY * 0.45;
                }}
                topWin.addEventListener('mousemove', onPointerMove);
                window.addEventListener('mousemove', onPointerMove);

                // 7. Render Loop (Smooth 60 FPS Animation)
                const clock = new THREE.Clock();

                function render() {{
                    requestAnimationFrame(render);
                    const elapsed = clock.getElapsedTime();

                    // Smooth parallax interpolation + subtle baseline rotation
                    group.rotation.y += (targetRotY - group.rotation.y) * 0.05 + 0.007;
                    group.rotation.x += (targetRotX - group.rotation.x) * 0.05;

                    // Inner octahedron counter-rotation and floating sine oscillation
                    octahedron.rotation.y -= 0.022;
                    octahedron.rotation.z += 0.014;
                    const floatY = Math.sin(elapsed * 2.2) * 0.11;
                    octahedron.position.y = floatY;
                    coreLight.position.y = floatY;

                    // Pulsing amber intelligence glow
                    const pulse = 2.4 + Math.sin(elapsed * 3.5) * 0.8;
                    coreLight.intensity = pulse;
                    octaMat.emissiveIntensity = 0.8 + Math.sin(elapsed * 3.5) * 0.35;

                    // Orbital ring subtle spin
                    ring.rotation.z += 0.006;

                    renderer.render(scene, camera);
                }}
                render();

                // Responsive Canvas Resize
                function onResize() {{
                    const w = wrapper.clientWidth || 800;
                    const h = wrapper.clientHeight || {height};
                    camera.aspect = w / h;
                    camera.updateProjectionMatrix();
                    renderer.setSize(w, h);
                }}
                window.addEventListener('resize', onResize);
                topWin.addEventListener('resize', onResize);
            }}

            if (document.readyState === 'loading') {{
                document.addEventListener('DOMContentLoaded', init);
            }} else {{
                init();
            }}
        }})();
        </script>
    </body>
    </html>
    """
    components.html(monolith_html, height=height, scrolling=False)


def render_sidebar_telemetry(custom_telemetry: Optional[Dict[str, Any]] = None):
    """Sleek, encapsulated UI telemetry widget for the Streamlit sidebar.

    Displays:
    1. Active Provider used for the last query (Gemini, OpenAI, DeepSeek, Groq, Ollama, Offline Heuristics).
    2. Response Latency in milliseconds with color coding (<800ms green, 800-2500ms yellow, >2500ms orange).
    3. Failover status badge if a primary provider failover occurred.
    """
    if custom_telemetry:
        telemetry = custom_telemetry
    elif "telemetry" in st.session_state and st.session_state["telemetry"]:
        telemetry = st.session_state["telemetry"]
    else:
        telemetry = get_last_telemetry()

    active_provider = telemetry.get("active_provider", "Google Gemini")
    primary_provider = telemetry.get("primary_provider", active_provider)
    latency_ms = float(telemetry.get("latency_ms", 0.0))
    failover_badge = telemetry.get("failover_badge")

    latency_color = get_latency_color(latency_ms)

    provider_icons = {
        "Google Gemini": "✨",
        "OpenAI": "🤖",
        "DeepSeek": "🧠",
        "Groq Cloud": "⚡",
        "Ollama (Local)": "🦙",
        "Offline Heuristics": "⚙️"
    }
    icon = provider_icons.get(active_provider, "🌐")

    st.sidebar.markdown("<hr class='enterprise-divider' />", unsafe_allow_html=True)
    st.sidebar.markdown(
        """
        <div style="text-align: center; font-size: 0.92rem; font-weight: 600; color: var(--text-color, #E2E8F0); margin-bottom: 8px;">
            📡 Routing & Telemetry
        </div>
        """,
        unsafe_allow_html=True
    )

    st.sidebar.markdown(
        f"""
        <div style="
            background-color: var(--bg-card, rgba(30, 41, 59, 0.7));
            border: 1px solid var(--border-soft, rgba(255, 255, 255, 0.1));
            border-radius: 14px;
            padding: 10px 14px;
            max-width: 260px;
            margin: 0 auto 8px auto;
            box-shadow: var(--shadow-card);
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="font-size: 0.76rem; color: var(--secondary-text-color, #94A3B8); font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em;">Active Provider</span>
                <span style="font-size: 0.88rem; font-weight: 600; color: var(--text-color, #E2E8F0);">{icon} {active_provider}</span>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 0.76rem; color: var(--secondary-text-color, #94A3B8); font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em;">Latency</span>
                <span style="
                    font-size: 0.82rem;
                    font-weight: 600;
                    color: {latency_color};
                    background-color: {latency_color}18;
                    padding: 2px 8px;
                    border-radius: 9999px;
                    border: 1px solid {latency_color}40;
                ">⏱️ {latency_ms:.1f} ms</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if failover_badge:
        st.sidebar.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, rgba(239, 68, 68, 0.15), rgba(245, 158, 11, 0.15));
                border: 1px solid rgba(245, 158, 11, 0.4);
                border-radius: 10px;
                padding: 6px 10px;
                max-width: 260px;
                margin: 4px auto 0 auto;
                font-size: 0.78rem;
                color: #FBBF24;
                font-weight: 500;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 6px;
            ">
                <span>⚡</span>
                <span><b>Failover:</b> {failover_badge}</span>
            </div>
            """,
            unsafe_allow_html=True
        )


# ---------------------------------------------------------------------------
# High-Priority AI Intelligence & Asset Diagnostics Components
# ---------------------------------------------------------------------------
def render_color_gradient_bar(swatches: List[Dict[str, Any]]) -> str:
    """Generates an HTML multi-stop CSS gradient bar reflecting extracted dominant colors."""
    if not swatches:
        return ""

    color_stops = []
    current_pct = 0.0
    for sw in swatches:
        hex_code = sw.get("hex", "#666666")
        pct = float(sw.get("percentage", 20.0))
        next_pct = min(100.0, current_pct + pct)
        color_stops.append(f"{hex_code} {current_pct:.1f}%")
        color_stops.append(f"{hex_code} {next_pct:.1f}%")
        current_pct = next_pct

    grad_css = ", ".join(color_stops)
    return f"""
    <div style="margin: 12px 0 16px 0;">
        <div style="
            display: flex;
            justify-content: space-between;
            font-size: 0.78rem;
            font-weight: 600;
            color: var(--text-secondary, #94A3B8);
            margin-bottom: 6px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        ">
            <span>Extracted Color Gamut Spectrum</span>
            <span>{len(swatches)} Dominant Tints</span>
        </div>
        <div style="
            height: 18px;
            width: 100%;
            border-radius: 9px;
            background: linear-gradient(to right, {grad_css});
            border: 1px solid var(--border-soft, rgba(255, 255, 255, 0.12));
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
        "></div>
    </div>
    """


def render_ai_intelligence_card(
    title: str,
    content: str,
    telemetry: Optional[Dict[str, Any]] = None,
    export_filename: Optional[str] = None,
    allow_download: bool = True,
    download_label: str = "💾 Download Intelligence Report (.md)",
    mime_type: str = "text/markdown"
) -> None:
    """Renders top-priority AI intelligence results with telemetry badges, copy/download actions."""
    if not content:
        return

    tel = telemetry or (st.session_state.get("telemetry") if hasattr(st, "session_state") else None) or get_last_telemetry()
    active_provider = tel.get("active_provider", "Offline Heuristics")
    latency_ms = float(tel.get("latency_ms", 0.0))
    failover_badge = tel.get("failover_badge")
    latency_color = get_latency_color(latency_ms)

    provider_icons = {
        "Google Gemini": "✨",
        "OpenAI": "🤖",
        "DeepSeek": "🧠",
        "Groq Cloud": "⚡",
        "Ollama (Local)": "🦙",
        "Offline Heuristics": "⚙️"
    }
    icon = provider_icons.get(active_provider, "🌐")

    # Header Row with Title and Telemetry Badges (Vertically Centered Flexbox)
    st.markdown(
        f"""
        <div style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
            margin: 8px 0 14px 0;
        ">
            <h3 style="margin: 0; font-weight: 600; color: var(--text-color, #FFFFFF); letter-spacing: -0.025em;">{title}</h3>
            <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                <span class="status-badge badge-sage">{icon} {active_provider}</span>
                <span style="
                    font-size: 0.82rem;
                    font-weight: 500;
                    color: {latency_color};
                    background-color: {latency_color}18;
                    padding: 5px 12px;
                    border-radius: 9999px;
                    border: 1px solid {latency_color}40;
                ">⏱️ {latency_ms:.1f} ms</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if failover_badge:
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, rgba(239, 68, 68, 0.15), rgba(245, 158, 11, 0.15));
                border: 1px solid rgba(245, 158, 11, 0.4);
                border-radius: 12px;
                padding: 10px 14px;
                margin-bottom: 16px;
                font-size: 0.82rem;
                color: #FBBF24;
                font-weight: 500;
            ">
                ⚡ <b>Failover Notice:</b> {failover_badge}
            </div>
            """,
            unsafe_allow_html=True
        )

    # Core AI Generated Response Focus Block (Unified 24px padding, 20px bottom margin)
    st.markdown(
        f"""<div class="focus-block" style="padding: 24px; margin-bottom: 20px;">{content}</div>""",
        unsafe_allow_html=True
    )

    # Quick Actions: Clean Left-Aligned Download Button
    if allow_download and export_filename:
        st.download_button(
            label=download_label,
            data=content,
            file_name=export_filename,
            mime=mime_type
        )


def render_image_diagnostics_panel(
    img_meta: Dict[str, Any],
    swatches: Optional[List[Dict[str, Any]]] = None,
    image: Optional[Any] = None,
    expanded: bool = False
) -> None:
    """Renders structured 2-column technical asset diagnostics:
    - Left Column: Visual thumbnail preview & key dimensions/geometry table.
    - Right Column: Continuous color spectrum gradient bar & dominant palette swatch chips.
    """
    with st.expander("📊 Image Properties & Color Analytics", expanded=expanded):
        col_left, col_right = st.columns([1, 1.25], gap="large")

        # -------------------------------------------------------------------
        # 1. Left Column: Visual Preview & Geometry
        # -------------------------------------------------------------------
        with col_left:
            st.markdown("##### 📐 Visual Asset & Geometry")
            if image is not None:
                st.image(image, width=280, caption=img_meta.get("filename", "Uploaded Asset"))

            dims = img_meta.get("dimensions", "Unknown")
            aspect = img_meta.get("aspect_ratio", "Unknown")
            mode = img_meta.get("mode", "RGB")
            fmt = img_meta.get("format", "JPEG")
            fsize = img_meta.get("file_size_formatted", img_meta.get("file_size", "Unknown"))
            mp = img_meta.get("megapixels", "N/A")

            st.markdown(
                f"""
                <div class="focus-block" style="padding: 14px 18px; margin-top: 10px;">
                    <table style="width: 100%; border-collapse: collapse; font-size: 0.88rem;">
                        <tr style="border-bottom: 1px solid var(--border-soft, rgba(255,255,255,0.08));">
                            <td style="color: var(--secondary-text-color, #94A3B8); padding: 7px 0; font-weight: 500;">Dimensions</td>
                            <td style="font-weight: 700; text-align: right; color: var(--text-color, #FFF);">{dims}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid var(--border-soft, rgba(255,255,255,0.08));">
                            <td style="color: var(--secondary-text-color, #94A3B8); padding: 7px 0; font-weight: 500;">Aspect Ratio</td>
                            <td style="font-weight: 700; text-align: right; color: var(--accent-sage, #87A878);">{aspect}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid var(--border-soft, rgba(255,255,255,0.08));">
                            <td style="color: var(--secondary-text-color, #94A3B8); padding: 7px 0; font-weight: 500;">Format & Mode</td>
                            <td style="font-weight: 700; text-align: right; color: var(--text-color, #FFF);">{fmt} | {mode}</td>
                        </tr>
                        <tr>
                            <td style="color: var(--secondary-text-color, #94A3B8); padding: 7px 0; font-weight: 500;">File Size</td>
                            <td style="font-weight: 700; text-align: right; color: var(--accent-ochre, #D4A574);">{fsize} ({mp} MP)</td>
                        </tr>
                    </table>
                </div>
                """,
                unsafe_allow_html=True
            )

        # -------------------------------------------------------------------
        # 2. Right Column: Color Spectrum & Palette Swatches
        # -------------------------------------------------------------------
        with col_right:
            st.markdown("##### 🎨 Color Spectrum & Swatches")

            if swatches:
                # Multi-stop continuous gradient bar
                st.markdown(render_color_gradient_bar(swatches), unsafe_allow_html=True)

                # Distinct color chips
                swatch_items = "".join([
                    f"""
                    <div style="
                        display: flex;
                        align-items: center;
                        gap: 12px;
                        padding: 8px 14px;
                        margin-bottom: 8px;
                        border-radius: 10px;
                        background-color: var(--bg-subtle, rgba(255,255,255,0.04));
                        border: 1px solid var(--border-soft, rgba(255,255,255,0.08));
                    ">
                        <div style="
                            width: 28px;
                            height: 28px;
                            border-radius: 6px;
                            background-color: {sw['hex']};
                            border: 1px solid rgba(255,255,255,0.25);
                            box-shadow: 0 2px 4px rgba(0,0,0,0.25);
                            flex-shrink: 0;
                        "></div>
                        <div style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
                            <span style="font-family: monospace; font-weight: 700; font-size: 0.9rem; color: var(--text-color, #FFF); letter-spacing: 0.04em;">{sw['hex']}</span>
                            <span style="font-size: 0.82rem; font-weight: 600; color: var(--secondary-text-color, #94A3B8);">{sw['percentage']}% coverage</span>
                        </div>
                    </div>
                    """
                    for sw in swatches[:5]
                ])

                st.markdown(swatch_items, unsafe_allow_html=True)
            else:
                st.caption("No color swatches extracted for this asset.")

        # Optional EXIF Camera Metadata Table
        exif = img_meta.get("exif", {})
        if exif:
            st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)
            st.markdown("##### 📷 EXIF Camera & Hardware Metadata")
            exif_items = "".join([
                f"<tr style='border-bottom: 1px solid var(--border-soft, rgba(255,255,255,0.06));'><td style='color: var(--secondary-text-color, #94A3B8); padding: 6px 0; font-weight: 500;'>{k}</td><td style='font-weight: 600; text-align: right; color: var(--text-color, #FFF);'>{v}</td></tr>"
                for k, v in exif.items()
            ])
            st.markdown(
                f"""
                <div class="focus-block" style="padding: 12px 18px;">
                    <table style="width: 100%; border-collapse: collapse; font-size: 0.85rem;">
                        {exif_items}
                    </table>
                </div>
                """,
                unsafe_allow_html=True
            )


def render_vision_analysis_card(
    analysis_text: str,
    telemetry: Optional[Dict[str, Any]] = None,
    image_metadata: Optional[Dict[str, Any]] = None,
    swatches: Optional[List[Dict[str, Any]]] = None,
    image: Optional[Any] = None,
    original_filename: Optional[str] = None
) -> None:
    """Renders multimodal vision results at the very top, followed by visual and technical asset properties below."""
    if not analysis_text:
        return

    # 1. Top Section: AI Intelligence Output (Hero Focus)
    fn = f"{original_filename or 'vision_analysis'}_report.md"
    render_ai_intelligence_card(
        title="🔍 Vision Intelligence Output",
        content=analysis_text,
        telemetry=telemetry,
        export_filename=fn,
        download_label="💾 Download Vision Analysis (.md)"
    )

    # 2. Divider / Visual Separation
    st.markdown("<hr class='enterprise-divider' />", unsafe_allow_html=True)

    # 3. Bottom Section: Visual & Technical Attributes
    if image_metadata or swatches:
        render_image_diagnostics_panel(
            img_meta=image_metadata or {},
            swatches=swatches or [],
            image=image,
            expanded=False
        )


def _render_audit_fragment_content():
    """Inner dashboard rendering function."""
    header_col1, header_col2 = st.columns([3, 1])
    with header_col1:
        st.markdown("### 🛡️ Enterprise Observability & Audit Dashboard")
        st.caption("Real-time telemetry, provider health diagnostics, and audit logs.")
    with header_col2:
        btn_refresh = st.button("🔄 Refresh Metrics", use_container_width=True)

    events = get_recent_events(limit=100)

    if not events:
        st.info("ℹ️ No runtime telemetry events recorded yet in `logs/telemetry.jsonl`. Execute queries in Document or Vision Studio to populate live analytics.")
        return

    df = pd.DataFrame(events)

    # -----------------------------------------------------------------------
    # 1. KPI Metric Cards
    # -----------------------------------------------------------------------
    total_inferences = len(df)
    success_count = (df["status_code"] == 200).sum() if "status_code" in df else total_inferences
    success_rate = (success_count / total_inferences) * 100 if total_inferences > 0 else 100.0

    latencies = df["latency_ms"].dropna().values if "latency_ms" in df else np.array([0.0])
    p95_latency = float(np.percentile(latencies, 95)) if len(latencies) > 0 else 0.0

    failover_count = (df["fallback_depth"] > 0).sum() if "fallback_depth" in df else 0
    failover_rate = (failover_count / total_inferences) * 100 if total_inferences > 0 else 0.0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Inferences", f"{total_inferences}", help="Last 100 recorded inference runs")
    with col2:
        st.metric("Success Rate", f"{success_rate:.1f}%", delta=f"{success_rate - 99.0:.1f}%" if success_rate < 99 else "Optimal")
    with col3:
        st.metric("p95 Latency", f"{p95_latency:.1f} ms", delta="-fast" if p95_latency < 1500 else "Slow", delta_color="inverse")
    with col4:
        st.metric("Failover Rate", f"{failover_rate:.1f}%", delta=f"{failover_count} failovers", delta_color="inverse")

    st.markdown("<hr class='enterprise-divider' />", unsafe_allow_html=True)

    # -----------------------------------------------------------------------
    # 2. Visualizations
    # -----------------------------------------------------------------------
    plot_col1, plot_col2 = st.columns(2)

    with plot_col1:
        st.markdown("#### 🎯 Provider Routing Distribution")
        if "provider_succeeded" in df:
            provider_counts = df["provider_succeeded"].value_counts().reset_index()
            provider_counts.columns = ["Provider", "Count"]
            fig_pie = px.pie(
                provider_counts,
                names="Provider",
                values="Count",
                hole=0.45,
                color_discrete_sequence=["#2563EB", "#10B981", "#8B5CF6", "#F59E0B", "#EC4899", "#64748B"]
            )
            fig_pie.update_layout(
                margin=dict(l=20, r=20, t=30, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#E2E8F0")
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    with plot_col2:
        st.markdown("#### ⚡ Latency Timeline & SLA (2500ms)")
        if "timestamp" in df and "latency_ms" in df:
            df_time = df.copy()
            df_time["timestamp"] = pd.to_datetime(df_time["timestamp"])
            fig_scatter = px.scatter(
                df_time,
                x="timestamp",
                y="latency_ms",
                color="provider_succeeded" if "provider_succeeded" in df_time else None,
                hover_data=["session_id", "fallback_depth", "status_code"],
                color_discrete_sequence=["#10B981", "#3B82F6", "#F59E0B", "#8B5CF6", "#EF4444"]
            )
            fig_scatter.add_hline(
                y=2500,
                line_dash="dash",
                line_color="#EF4444",
                annotation_text="2500ms SLA Threshold",
                annotation_position="top left"
            )
            fig_scatter.update_layout(
                margin=dict(l=20, r=20, t=30, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis_title="Execution Timestamp",
                yaxis_title="Latency (ms)",
                font=dict(color="#E2E8F0")
            )
            st.plotly_chart(fig_scatter, use_container_width=True)

    # 3. Failover & Error Breakdown
    st.markdown("#### 🔄 Failover Cascades & Dispatched Fallbacks")
    failover_df = df[df["fallback_depth"] > 0]
    if not failover_df.empty:
        fig_bar = px.bar(
            failover_df,
            x="provider_attempted",
            y="latency_ms",
            color="provider_succeeded",
            barmode="group",
            title="Failover Execution Latencies (Attempted vs Succeeded)",
            hover_data=["error_message", "status_code"]
        )
        fig_bar.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#E2E8F0")
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.success("✅ **Zero Failovers Encountered**: All primary providers completed queries directly without requiring fallback cascades.")

    # -----------------------------------------------------------------------
    # 4. Audit Log Table with Filters & Download
    # -----------------------------------------------------------------------
    st.markdown("<hr class='enterprise-divider' />", unsafe_allow_html=True)
    st.markdown("#### 📋 Searchable Audit Log")

    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        provider_filter = st.multiselect(
            "Filter by Provider Succeeded:",
            options=df["provider_succeeded"].unique().tolist() if "provider_succeeded" in df else [],
            default=[]
        )
    with filter_col2:
        status_filter = st.multiselect(
            "Filter by Status Code:",
            options=df["status_code"].unique().tolist() if "status_code" in df else [],
            default=[]
        )

    filtered_df = df.copy()
    if provider_filter:
        filtered_df = filtered_df[filtered_df["provider_succeeded"].isin(provider_filter)]
    if status_filter:
        filtered_df = filtered_df[filtered_df["status_code"].isin(status_filter)]

    # Clean display columns
    display_cols = [c for c in ["timestamp", "session_id", "provider_attempted", "provider_succeeded", "fallback_depth", "latency_ms", "status_code", "payload_hash", "error_message"] if c in filtered_df.columns]
    st.dataframe(
        filtered_df[display_cols],
        use_container_width=True,
        hide_index=True
    )

    # Download buttons
    dl_col1, dl_col2 = st.columns(2)
    with dl_col1:
        csv_data = filtered_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Download Audit Log (CSV)",
            data=csv_data,
            file_name="audit_telemetry.csv",
            mime="text/csv",
            use_container_width=True
        )
    with dl_col2:
        jsonl_data = "\n".join([json.dumps(e) for e in events]).encode("utf-8")
        st.download_button(
            "📥 Download Raw Events (JSONL)",
            data=jsonl_data,
            file_name="telemetry.jsonl",
            mime="application/json",
            use_container_width=True
        )


def render_admin_audit_dashboard():
    """Renders the Admin Audit & Observability Dashboard.
    Uses @st.fragment when supported for isolated re-renders.
    """
    if hasattr(st, "fragment"):
        @st.fragment
        def _frag():
            _render_audit_fragment_content()
        _frag()
    else:
        _render_audit_fragment_content()


# ---------------------------------------------------------------------------
# Multi-Format Enterprise Export Helpers (DOCX & Executive PDF)
# ---------------------------------------------------------------------------
def _clean_text_for_pdf(text: str) -> str:
    """Sanitizes text for FPDF rendering by replacing emojis and normalizing characters."""
    if not text:
        return ""
    replacements = {
        "📊": "[Data]",
        "⚡": "[Fast]",
        "🔍": "[Inspect]",
        "📝": "[Note]",
        "🛡️": "[Security]",
        "👁️": "[Vision]",
        "📄": "[Doc]",
        "💾": "[Save]",
        "🎯": "[Target]",
        "📌": "[Key]",
        "🔬": "[Analysis]",
        "⚠️": "[Warning]",
        "✅": "[Pass]",
        "🟢": "[Active]",
        "💻": "[Local]",
        "🧠": "[AI]",
        "✨": "*",
        "•": "-",
        "–": "-",
        "—": "-",
        '"': '"',
        '"': '"',
        ''': "'",
        ''': "'"
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    text = re.sub(r'[\U00010000-\U0010ffff]', '', text)
    return text


def _add_formatted_runs_docx(paragraph, text: str) -> None:
    """Parses simple inline markdown formatting (**bold** and `code`) into docx runs."""
    from docx.shared import Pt, RGBColor
    tokens = re.split(r"(\*\*.*?\*\*|`.*?`)", text)
    for token in tokens:
        if not token:
            continue
        if token.startswith("**") and token.endswith("**") and len(token) >= 4:
            run = paragraph.add_run(token[2:-2])
            run.font.name = "Arial"
            run.bold = True
        elif token.startswith("`") and token.endswith("`") and len(token) >= 2:
            run = paragraph.add_run(token[1:-1])
            run.font.name = "Consolas"
            run.font.size = Pt(9.5)
            run.font.color.rgb = RGBColor(224, 83, 0)
        else:
            run = paragraph.add_run(token)
            run.font.name = "Arial"


def export_markdown_to_docx(content: str, title: str = "Artifact Document") -> io.BytesIO:
    """Converts Markdown artifact text into a professionally styled DOCX document in-memory."""
    try:
        from docx import Document
        from docx.shared import Inches, Pt, RGBColor
        from docx.enum.table import WD_TABLE_ALIGNMENT
        from docx.oxml import parse_xml
        from docx.oxml.ns import nsdecls
    except ImportError:
        raise RuntimeError("`python-docx` is not installed.")

    doc = Document()

    # 1-inch margins
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # Document Header / Brand Accent
    header_p = doc.add_paragraph()
    clean_title = title.replace("\n", " ").strip()
    h_run = header_p.add_run(f"MULTIMODAL INTELLIGENCE STUDIO  |  {clean_title.upper()}")
    h_run.font.name = "Arial"
    h_run.font.size = Pt(8.5)
    h_run.font.bold = True
    h_run.font.color.rgb = RGBColor(224, 83, 0)
    header_p.paragraph_format.space_after = Pt(14)

    lines = content.splitlines()
    i = 0
    num_lines = len(lines)

    while i < num_lines:
        line = lines[i].strip()

        if not line:
            i += 1
            continue

        # 1. Horizontal Rules
        if line in ("---", "***", "___"):
            div_p = doc.add_paragraph()
            div_p.paragraph_format.space_after = Pt(6)
            i += 1
            continue

        # 2. Markdown Tables
        if line.startswith("|") and line.endswith("|"):
            table_lines = []
            while i < num_lines and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
                table_lines.append(lines[i].strip())
                i += 1

            rows_data = []
            for tl in table_lines:
                if re.match(r"^\|(?:\s*:?-+:?\s*\|)+$", tl):
                    continue
                raw_cells = tl.strip("|").split("|")
                cleaned_cells = [c.strip().replace("**", "") for c in raw_cells]
                if cleaned_cells:
                    rows_data.append(cleaned_cells)

            if rows_data:
                col_count = max(len(r) for r in rows_data)
                tbl = doc.add_table(rows=len(rows_data), cols=col_count)
                tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
                tbl.autofit = True

                for row_idx, r_data in enumerate(rows_data):
                    is_header = (row_idx == 0)
                    for col_idx in range(col_count):
                        val = r_data[col_idx] if col_idx < len(r_data) else ""
                        cell = tbl.cell(row_idx, col_idx)
                        cell.text = val
                        p = cell.paragraphs[0]
                        p.paragraph_format.space_before = Pt(4)
                        p.paragraph_format.space_after = Pt(4)
                        if p.runs:
                            p.runs[0].font.name = "Arial"
                            p.runs[0].font.size = Pt(9.5)
                            if is_header:
                                p.runs[0].font.bold = True
                                p.runs[0].font.color.rgb = RGBColor(255, 255, 255)
                                shading = parse_xml(r'<w:shd {} w:fill="2A2D34"/>'.format(nsdecls('w')))
                                cell._tc.get_or_add_tcPr().append(shading)
                            else:
                                if row_idx % 2 == 1:
                                    shading = parse_xml(r'<w:shd {} w:fill="F8F9FA"/>'.format(nsdecls('w')))
                                    cell._tc.get_or_add_tcPr().append(shading)

                doc.add_paragraph().paragraph_format.space_after = Pt(6)
            continue

        # 3. Headings
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            text = line.lstrip("#").strip().replace("**", "").replace("*", "")
            h_p = doc.add_paragraph()
            h_run = h_p.add_run(text)
            h_run.font.name = "Arial"
            h_run.bold = True

            if level == 1:
                h_run.font.size = Pt(17)
                h_run.font.color.rgb = RGBColor(224, 83, 0)
                h_p.paragraph_format.space_before = Pt(14)
                h_p.paragraph_format.space_after = Pt(6)
            elif level == 2:
                h_run.font.size = Pt(13.5)
                h_run.font.color.rgb = RGBColor(30, 41, 59)
                h_p.paragraph_format.space_before = Pt(10)
                h_p.paragraph_format.space_after = Pt(4)
            else:
                h_run.font.size = Pt(11.5)
                h_run.font.color.rgb = RGBColor(51, 65, 85)
                h_p.paragraph_format.space_before = Pt(8)
                h_p.paragraph_format.space_after = Pt(3)

            i += 1
            continue

        # 4. Bullet lists
        if line.startswith("- ") or line.startswith("* "):
            bullet_text = line[2:].strip()
            b_p = doc.add_paragraph(style="List Bullet")
            b_p.paragraph_format.space_after = Pt(3)
            _add_formatted_runs_docx(b_p, bullet_text)
            i += 1
            continue

        # 5. Numbered lists
        num_match = re.match(r"^(\d+)\.\s+(.*)", line)
        if num_match:
            num_text = num_match.group(2).strip()
            n_p = doc.add_paragraph(style="List Number")
            n_p.paragraph_format.space_after = Pt(3)
            _add_formatted_runs_docx(n_p, num_text)
            i += 1
            continue

        # 6. Blockquotes
        if line.startswith(">"):
            quote_text = line.lstrip("> ").strip()
            q_p = doc.add_paragraph()
            q_p.paragraph_format.left_indent = Inches(0.35)
            q_p.paragraph_format.space_after = Pt(6)
            run = q_p.add_run(f'"{quote_text}"')
            run.font.name = "Arial"
            run.italic = True
            run.font.color.rgb = RGBColor(100, 116, 139)
            i += 1
            continue

        # 7. Standard Paragraph
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.line_spacing = 1.15
        _add_formatted_runs_docx(p, line)
        i += 1

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer


def export_markdown_to_pdf(content: str, title: str = "Artifact Document") -> io.BytesIO:
    """Converts Markdown artifact text into an executive styled PDF document in-memory."""
    try:
        from fpdf import FPDF
        from fpdf.enums import XPos, YPos
    except ImportError:
        raise RuntimeError("`fpdf2` is not installed.")

    class ExecutivePDF(FPDF):
        def __init__(self, doc_title: str):
            super().__init__(orientation="P", unit="mm", format="A4")
            self.doc_title = doc_title
            self.set_margins(16, 16, 16)
            self.set_auto_page_break(auto=True, margin=16)
            self.base_font = "Helvetica"
            if os.path.exists("C:/Windows/Fonts/arial.ttf"):
                try:
                    self.add_font("CustomArial", "", "C:/Windows/Fonts/arial.ttf")
                    if os.path.exists("C:/Windows/Fonts/arialbd.ttf"):
                        self.add_font("CustomArial", "B", "C:/Windows/Fonts/arialbd.ttf")
                    if os.path.exists("C:/Windows/Fonts/ariali.ttf"):
                        self.add_font("CustomArial", "I", "C:/Windows/Fonts/ariali.ttf")
                    self.base_font = "CustomArial"
                except Exception:
                    self.base_font = "Helvetica"

        def header(self):
            self.set_font(self.base_font, "B" if self.base_font != "Helvetica" else "", 8)
            self.set_text_color(224, 83, 0)
            clean_hdr = _clean_text_for_pdf(self.doc_title)
            self.cell(0, 6, f"MULTIMODAL INTELLIGENCE STUDIO  |  {clean_hdr.upper()}", border="B", align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.ln(3)

        def footer(self):
            self.set_y(-12)
            self.set_font(self.base_font, "", 8)
            self.set_text_color(148, 163, 184)
            self.cell(0, 8, f"Executive Artifact Dossier  -  Page {self.page_no()}", border=0, align="C")

    pdf = ExecutivePDF(title)
    pdf.add_page()
    bf = pdf.base_font

    lines = content.splitlines()
    i = 0
    num_lines = len(lines)

    while i < num_lines:
        line = lines[i].strip()
        if not line:
            pdf.ln(2)
            i += 1
            continue

        # 1. Horizontal Rules
        if line in ("---", "***", "___"):
            pdf.set_draw_color(220, 225, 235)
            pdf.line(16, pdf.get_y(), 194, pdf.get_y())
            pdf.ln(4)
            i += 1
            continue

        # 2. Markdown Tables
        if line.startswith("|") and line.endswith("|"):
            table_lines = []
            while i < num_lines and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
                table_lines.append(lines[i].strip())
                i += 1

            rows_data = []
            for tl in table_lines:
                if re.match(r"^\|(?:\s*:?-+:?\s*\|)+$", tl):
                    continue
                raw_cells = tl.strip("|").split("|")
                cleaned_cells = [_clean_text_for_pdf(c.strip().replace("**", "")) for c in raw_cells]
                if cleaned_cells:
                    rows_data.append(cleaned_cells)

            if rows_data:
                col_count = max(len(r) for r in rows_data)
                padded_rows = []
                for r in rows_data:
                    padded_r = r + [""] * (col_count - len(r))
                    padded_rows.append(padded_r)

                pdf.set_font(bf, "", 9)
                pdf.set_text_color(30, 41, 59)
                try:
                    with pdf.table(padded_rows, text_align="LEFT") as table:
                        pass
                except Exception:
                    for r in padded_rows:
                        pdf.multi_cell(0, 5, " | ".join(r))
                pdf.ln(3)
            continue

        # 3. Headings
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            text = _clean_text_for_pdf(line.lstrip("#").strip().replace("**", "").replace("*", ""))

            if level == 1:
                pdf.set_font(bf, "B", 15)
                pdf.set_text_color(224, 83, 0)
                pdf.multi_cell(0, 8, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.ln(2)
            elif level == 2:
                pdf.set_font(bf, "B", 12.5)
                pdf.set_text_color(30, 41, 59)
                pdf.multi_cell(0, 7, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.ln(2)
            else:
                pdf.set_font(bf, "B", 10.5)
                pdf.set_text_color(51, 65, 85)
                pdf.multi_cell(0, 6, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.ln(1)

            i += 1
            continue

        # 4. Bullet lists
        if line.startswith("- ") or line.startswith("* "):
            item_text = _clean_text_for_pdf(line[2:].strip().replace("**", ""))
            pdf.set_font(bf, "", 9.5)
            pdf.set_text_color(33, 37, 41)
            pdf.multi_cell(0, 5, f"   -  {item_text}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            i += 1
            continue

        # 5. Numbered lists
        num_match = re.match(r"^(\d+)\.\s+(.*)", line)
        if num_match:
            n_idx = num_match.group(1)
            item_text = _clean_text_for_pdf(num_match.group(2).strip().replace("**", ""))
            pdf.set_font(bf, "", 9.5)
            pdf.set_text_color(33, 37, 41)
            pdf.multi_cell(0, 5, f"   {n_idx}.  {item_text}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            i += 1
            continue

        # 6. Blockquotes
        if line.startswith(">"):
            q_text = _clean_text_for_pdf(line.lstrip("> ").strip())
            pdf.set_font(bf, "I" if bf != "Helvetica" else "", 9)
            pdf.set_text_color(100, 116, 139)
            pdf.multi_cell(0, 5, f'   "{q_text}"', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(1)
            i += 1
            continue

        # 7. Standard Paragraph
        p_text = _clean_text_for_pdf(line.replace("**", ""))
        pdf.set_font(bf, "", 9.5)
        pdf.set_text_color(33, 37, 41)
        pdf.multi_cell(0, 5.5, p_text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(1)
        i += 1

    buffer = io.BytesIO(bytes(pdf.output()))
    return buffer


def compute_markdown_diff_html(old_text: str, new_text: str) -> str:
    """Computes a line-by-line visual unified diff between two text versions.
    Renders additions in green (+), deletions in red strikethrough (-),
    chunk headers in amber pills (@@), and unchanged lines in muted monospace text.
    """
    old_lines = (old_text or "").splitlines(keepends=True)
    new_lines = (new_text or "").splitlines(keepends=True)

    diff = list(difflib.unified_diff(old_lines, new_lines, fromfile="Base Version", tofile="Target Version", n=3))

    if not diff:
        return (
            '<div class="diff-inspector-container" style="max-height: 520px; overflow-y: auto; padding: 24px; text-align: center; border-radius: 14px; background: rgba(18, 20, 26, 0.85); backdrop-filter: blur(20px); border: 1px solid rgba(255, 140, 40, 0.2);">'
            '<div style="color: var(--secondary-text-color, #A1A1A6); font-family: var(--font-main, sans-serif); font-size: 0.92rem;">'
            '✨ <b>Identical Versions:</b> No textual differences detected between the selected versions.'
            '</div>'
            '</div>'
        )

    html_lines = []
    for line in diff:
        raw_line = line.rstrip("\r\n")
        escaped = html.escape(raw_line) if raw_line else "&nbsp;"

        if raw_line.startswith("@@"):
            html_lines.append(
                f'<div class="diff-line diff-chunk" style="color: #FFAA55; background: rgba(255, 140, 40, 0.15); font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 0.84rem; padding: 4px 10px; margin: 6px 0 3px 0; border-radius: 6px; font-weight: 600; display: inline-block;">{escaped}</div>'
            )
        elif raw_line.startswith("+++") or raw_line.startswith("---"):
            html_lines.append(
                f'<div class="diff-line diff-meta" style="color: #8E8E93; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 0.80rem; padding: 2px 8px; margin: 1px 0; font-weight: 500;">{escaped}</div>'
            )
        elif raw_line.startswith("+"):
            html_lines.append(
                f'<div class="diff-line diff-add" style="color: #30D158; background: rgba(48, 209, 88, 0.15); border-left: 3px solid #30D158; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 0.86rem; padding: 3px 10px; margin: 1px 0; border-radius: 0 4px 4px 0; white-space: pre-wrap; word-break: break-word;">{escaped}</div>'
            )
        elif raw_line.startswith("-"):
            html_lines.append(
                f'<div class="diff-line diff-del" style="color: #FF453A; background: rgba(255, 69, 58, 0.15); border-left: 3px solid #FF453A; text-decoration: line-through; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 0.86rem; padding: 3px 10px; margin: 1px 0; border-radius: 0 4px 4px 0; white-space: pre-wrap; word-break: break-word;">{escaped}</div>'
            )
        else:
            html_lines.append(
                f'<div class="diff-line diff-same" style="color: #A1A1A6; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 0.86rem; padding: 2px 10px; margin: 1px 0; white-space: pre-wrap; word-break: break-word;">{escaped}</div>'
            )

    content_html = "\n".join(html_lines)
    return (
        f'<div class="diff-inspector-container" style="max-height: 520px; overflow-y: auto; overflow-x: auto; padding: 16px 18px; border-radius: 14px; background: rgba(18, 20, 26, 0.85); backdrop-filter: blur(20px); border: 1px solid rgba(255, 140, 40, 0.2); box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.3);">'
        f'{content_html}'
        f'</div>'
    )


# ---------------------------------------------------------------------------
# Stateful In-Place Claude Artifacts Workspace Component
# ---------------------------------------------------------------------------
def set_initial_artifact(
    title: str,
    content: str,
    observations: Optional[Dict[str, Any]] = None,
    force_reset: bool = False
) -> None:
    """Initializes or updates the stateful Claude Artifact workspace state (v1)."""
    if not content or not str(content).strip():
        return

    content_clean = str(content).strip()
    obs_clean = observations or {}

    # Fingerprint to distinguish between different documents vs reruns
    content_fingerprint = f"{title}_{len(content_clean)}_{content_clean[:80]}"
    prev_fingerprint = st.session_state.get("_artifact_fingerprint")

    if force_reset or "artifact_versions" not in st.session_state or not st.session_state.artifact_versions or prev_fingerprint != content_fingerprint:
        st.session_state.artifact_versions = [content_clean]
        st.session_state.artifact_version_idx = 0
        st.session_state.artifact_title = title or "Document Artifact"
        st.session_state.artifact_observations = obs_clean
        st.session_state["_artifact_fingerprint"] = content_fingerprint


def render_claude_artifact_workspace(
    router: Any,
    preferred_provider: str = "Google Gemini",
    key_prefix: str = "artifact"
) -> None:
    """Renders the stateful in-place Claude Artifacts workspace:
    - Version navigation (v1, v2, ...) with rollback support
    - Dual-mode segmented control: [👁️ Preview] vs [📝 Edit Source]
    - In-line AI Co-pilot with quick actions & custom natural-language instructions
    - Direct export of active markdown version
    """
    if "artifact_versions" not in st.session_state or not st.session_state.artifact_versions:
        return

    versions: List[str] = st.session_state.artifact_versions
    total_versions = len(versions)
    idx = int(st.session_state.get("artifact_version_idx", 0))

    if idx < 0:
        idx = 0
    elif idx >= total_versions:
        idx = total_versions - 1
    st.session_state.artifact_version_idx = idx

    current_content = versions[idx]
    title = st.session_state.get("artifact_title", "Document Artifact")
    observations = st.session_state.get("artifact_observations", {})

    st.markdown("<hr class='enterprise-divider' />", unsafe_allow_html=True)

    # 1. Glassmorphic Header Card
    obs_pills = ""
    if observations:
        pill_items = []
        for k, v in list(observations.items())[:3]:
            val_str = str(v)
            if isinstance(v, list):
                val_str = ", ".join([str(x) for x in v[:2]])
            pill_items.append(f"<span class='status-badge badge-neutral' style='font-size:0.75rem; padding: 2px 8px;'>{k}: {val_str}</span>")
        obs_pills = f"<div style='display:flex; gap:6px; flex-wrap:wrap; margin-top:8px;'>{''.join(pill_items)}</div>"

    st.markdown(
        f"""
        <div style="
            background: var(--bg-card);
            backdrop-filter: blur(28px) saturate(200%);
            -webkit-backdrop-filter: blur(28px) saturate(200%);
            border: 1px solid var(--border-soft);
            border-top: 1px solid var(--border-top);
            border-radius: 18px;
            padding: 16px 22px;
            margin-bottom: 14px;
            box-shadow: var(--shadow-card);
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
                    <span style="font-size: 1.35rem;">📄</span>
                    <span style="font-size: 1.15rem; font-weight: 600; color: var(--text-color); letter-spacing: -0.02em;">
                        {title}
                    </span>
                    <span class="status-badge badge-amber" style="font-size: 0.78rem; padding: 3px 10px; font-weight: 600;">
                        v{idx + 1} of {total_versions}
                    </span>
                </div>
            </div>
            {obs_pills}
        </div>
        """,
        unsafe_allow_html=True
    )

    # 2. Controls Row with Multi-Format Enterprise Export
    ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4, ctrl_col5 = st.columns([1.9, 1.15, 0.65, 1.25, 0.85])

    with ctrl_col1:
        view_mode = st.radio(
            "Artifact View Mode",
            options=["👁️ Preview", "📝 Edit Source", "🔍 Compare Diff"],
            horizontal=True,
            label_visibility="collapsed",
            key=f"{key_prefix}_view_mode_toggle"
        )

    with ctrl_col2:
        ver_options = [f"Version {i + 1}{' (Active)' if i == idx else ''}" for i in range(total_versions)]
        selected_ver_label = st.selectbox(
            "Version History",
            options=ver_options,
            index=idx,
            label_visibility="collapsed",
            key=f"{key_prefix}_ver_select"
        )
        selected_idx = ver_options.index(selected_ver_label)

    with ctrl_col3:
        btn_rollback = st.button("↩️ Revert", use_container_width=True, key=f"{key_prefix}_btn_rollback", help="Revert to selected version")
        prev_chosen_idx = st.session_state.get(f"_{key_prefix}_last_selected_ver", idx)
        if (btn_rollback or selected_idx != prev_chosen_idx) and selected_idx != idx:
            st.session_state.artifact_version_idx = selected_idx
            st.session_state[f"_{key_prefix}_last_selected_ver"] = selected_idx
            st.rerun()

    with ctrl_col4:
        export_format = st.selectbox(
            "Export Format",
            options=["Markdown (.md)", "Word Document (.docx)", "Executive PDF (.pdf)"],
            index=0,
            label_visibility="collapsed",
            key=f"{key_prefix}_export_fmt_select",
            help="Select export file format"
        )

    with ctrl_col5:
        clean_fn = title.lower().replace(" ", "_").replace("/", "_")
        v_tag = f"v{idx + 1}"

        if export_format == "Word Document (.docx)":
            docx_buf = export_markdown_to_docx(content=current_content, title=title)
            export_data = docx_buf.getvalue()
            export_name = f"{clean_fn}_{v_tag}.docx"
            export_mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif export_format == "Executive PDF (.pdf)":
            pdf_buf = export_markdown_to_pdf(content=current_content, title=title)
            export_data = pdf_buf.getvalue()
            export_name = f"{clean_fn}_{v_tag}.pdf"
            export_mime = "application/pdf"
        else:
            export_data = current_content.encode("utf-8")
            export_name = f"{clean_fn}_{v_tag}.md"
            export_mime = "text/markdown"

        st.download_button(
            "💾 Export",
            data=export_data,
            file_name=export_name,
            mime=export_mime,
            use_container_width=True,
            key=f"{key_prefix}_btn_export_dynamic"
        )


    # 3. Canvas Body
    if view_mode == "👁️ Preview":
        st.markdown(
            f"""
            <div class="focus-block" style="
                min-height: 220px;
                padding: 24px 28px;
                border-radius: 18px;
                margin: 6px 0 16px 0;
                background-color: var(--bg-card);
                border: 1px solid var(--border-soft);
                box-shadow: var(--shadow-card);
            ">
            """,
            unsafe_allow_html=True
        )
        st.markdown(current_content)
        st.markdown("</div>", unsafe_allow_html=True)
    elif view_mode == "📝 Edit Source":
        st.markdown("<p style='font-size:0.84rem; color:var(--secondary-text-color); margin: 4px 0 6px 0;'>Directly modify Markdown artifact content below:</p>", unsafe_allow_html=True)
        edited_text = st.text_area(
            "Direct Artifact Source Editor",
            value=current_content,
            height=360,
            key=f"{key_prefix}_editor_{idx}",
            label_visibility="collapsed"
        )
        if st.button("💾 Save Manual Changes", key=f"{key_prefix}_btn_save_manual", type="primary"):
            if edited_text.strip() and edited_text.strip() != current_content.strip():
                st.session_state.artifact_versions.append(edited_text.strip())
                st.session_state.artifact_version_idx = len(st.session_state.artifact_versions) - 1
                st.session_state[f"_{key_prefix}_last_selected_ver"] = len(st.session_state.artifact_versions) - 1
                st.success(f"✅ Committed manual modifications as Version {len(st.session_state.artifact_versions)}!")
                st.rerun()
            elif not edited_text.strip():
                st.warning("Cannot commit an empty document.")
            else:
                st.info("No modifications detected.")
    elif view_mode == "🔍 Compare Diff":
        if total_versions < 2:
            st.markdown(
                """
                <div style="
                    padding: 16px 20px;
                    border-radius: 14px;
                    background: rgba(255, 122, 0, 0.08);
                    border: 1px solid rgba(255, 122, 0, 0.3);
                    color: #FFAA55;
                    font-size: 0.9rem;
                    margin: 8px 0 16px 0;
                    display: flex;
                    align-items: center;
                    gap: 12px;
                ">
                    <span style="font-size: 1.25rem;">💡</span>
                    <span><b>Single Version Active:</b> At least two artifact versions are required to compute a visual diff. Use the In-Line Co-Pilot below or switch to <b>📝 Edit Source</b> to create a new revision.</span>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            diff_col1, diff_col2 = st.columns(2)
            default_base_idx = max(0, idx - 1) if idx > 0 else 0
            default_target_idx = idx if idx != default_base_idx else min(total_versions - 1, default_base_idx + 1)

            with diff_col1:
                base_idx = st.selectbox(
                    "Base Version (Original / -)",
                    options=list(range(total_versions)),
                    index=default_base_idx,
                    format_func=lambda i: f"Version {i + 1}{' (Initial)' if i == 0 else ''}",
                    key=f"{key_prefix}_diff_base_idx"
                )
            with diff_col2:
                target_idx = st.selectbox(
                    "Target Version (Modified / +)",
                    options=list(range(total_versions)),
                    index=default_target_idx,
                    format_func=lambda i: f"Version {i + 1}{' (Active)' if i == idx else ''}",
                    key=f"{key_prefix}_diff_target_idx"
                )

            old_text = versions[base_idx]
            new_text = versions[target_idx]
            diff_html = compute_markdown_diff_html(old_text, new_text)
            st.markdown(diff_html, unsafe_allow_html=True)

    # 4. In-Line Co-Pilot Toolbar
    st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 8px; margin: 12px 0 8px 0;">
            <span style="font-size: 1rem;">⚡</span>
            <span style="font-size: 0.92rem; font-weight: 600; color: var(--text-color);">
                In-Line Artifact Co-Pilot
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

    action_to_dispatch = None

    qcol1, qcol2, qcol3, qcol4 = st.columns(4)
    with qcol1:
        if st.button("📊 Convert to Table", use_container_width=True, key=f"{key_prefix}_qp_table"):
            action_to_dispatch = "Convert the data, figures, and key findings in this document into clear, well-structured Markdown tables."
    with qcol2:
        if st.button("⚡ Executive Summary", use_container_width=True, key=f"{key_prefix}_qp_exec"):
            action_to_dispatch = "Condense and restructure this document into a high-level Executive Summary with key metrics, highlights, and operational implications."
    with qcol3:
        if st.button("🔍 Highlight Anomalies", use_container_width=True, key=f"{key_prefix}_qp_anom"):
            action_to_dispatch = "Analyze and explicitly highlight all anomalies, risks, discrepancies, outliers, and variance flags."
    with qcol4:
        if st.button("📝 Make Tone Formal", use_container_width=True, key=f"{key_prefix}_qp_formal"):
            action_to_dispatch = "Rewrite this document using a formal, executive, enterprise-grade professional tone, removing casual language."

    with st.form(key=f"{key_prefix}_copilot_prompt_form", clear_on_submit=False):
        p_col1, p_col2 = st.columns([4.2, 1.2])
        with p_col1:
            custom_instruction = st.text_input(
                "✨ How should the AI modify this document?",
                placeholder="e.g. 'Add an executive table', 'Translate to French', 'Extract operational risks'",
                key=f"{key_prefix}_custom_instruction_text",
                label_visibility="collapsed"
            )
        with p_col2:
            btn_submit_copilot = st.form_submit_button("✨ Transform", use_container_width=True, type="primary")

        if btn_submit_copilot and custom_instruction.strip():
            action_to_dispatch = custom_instruction.strip()

    if action_to_dispatch:
        with st.spinner(f"Transforming artifact to v{total_versions + 1} via {preferred_provider}..."):
            try:
                obs_dict = st.session_state.get("artifact_observations", {})
                if hasattr(router, "transform_artifact"):
                    transformed = router.transform_artifact(
                        current_content=current_content,
                        observations=obs_dict,
                        user_instruction=action_to_dispatch,
                        preferred_provider=preferred_provider
                    )
                else:
                    from core.llm_router import LLMRouter
                    transformed = LLMRouter.transform_artifact(
                        current_content=current_content,
                        observations=obs_dict,
                        user_instruction=action_to_dispatch,
                        preferred_provider=preferred_provider
                    )

                if transformed and transformed.strip():
                    st.session_state.artifact_versions.append(transformed.strip())
                    st.session_state.artifact_version_idx = len(st.session_state.artifact_versions) - 1
                    st.session_state[f"_{key_prefix}_last_selected_ver"] = len(st.session_state.artifact_versions) - 1
                    st.success(f"✅ Generated Version {len(st.session_state.artifact_versions)}!")
                    st.rerun()
                else:
                    st.error("Transformation returned empty content.")
            except Exception as exc:
                st.error(f"Error during artifact transformation: {exc}")

