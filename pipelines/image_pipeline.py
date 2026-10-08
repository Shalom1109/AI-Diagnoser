"""pipelines/image_pipeline.py

Image analysis and vision processing pipeline for Multimodal Document Analysis.
Features:
1. Pillow (PIL) ingestion for PNG, JPG, JPEG, WEBP with auto-orientation.
2. Metadata extraction (dimensions, megapixels, aspect ratio, format, color mode, EXIF).
3. Dominant color extraction & palette swatch generation with hex codes and percentages.
4. Vision & OCR interface connecting with `core.llm_router.query_llm`.
"""

import gc
import io
import os
import tempfile
from collections import Counter
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple, Union
from PIL import Image, ImageOps, ExifTags

from core.llm_router import (
    LLMRouter,
    route_vision_request,
    query_llm,
    get_last_telemetry,
    encode_image_to_base64,
    _prepare_pil_image
)

SUPPORTED_IMAGE_EXTENSIONS = [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"]
SUPPORTED_IMAGE_MIMES = ["image/png", "image/jpeg", "image/webp", "image/bmp", "image/tiff"]


# ---------------------------------------------------------------------------
# 0. Memory Leak Safeguards & Session Cleanup Routines
# ---------------------------------------------------------------------------
def clean_session_buffers():
    """Explicit cleanup routine that frees large BytesIO streams, PIL Image instances,
    and base64 strings stored in st.session_state once an inference run finishes.
    """
    try:
        import streamlit as st
        if hasattr(st, "session_state"):
            buffer_keys = [
                "last_image_buffer", "raw_image_bytes", "image_base64",
                "cached_image_obj", "document_raw_bytes", "temp_file_path"
            ]
            for key in buffer_keys:
                if key in st.session_state:
                    val = st.session_state[key]
                    if hasattr(val, "close"):
                        try:
                            val.close()
                        except Exception:
                            pass
                    del st.session_state[key]
    except Exception:
        pass
    gc.collect()


def maybe_collect_garbage(file_size_bytes: Optional[int] = None):
    """Force garbage collection after processing files exceeding 5MB to reclaim RAM."""
    if file_size_bytes and file_size_bytes > 5 * 1024 * 1024:
        gc.collect()


@contextmanager
def safe_temp_file_context(file_bytes: bytes, suffix: str = ".tmp"):
    """Disk-backed temporary caching via tempfile.NamedTemporaryFile with context manager
    ensuring guaranteed file deletion and memory reclaiming.
    """
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        tmp_file.write(file_bytes)
        tmp_file.flush()
        tmp_file.close()
        yield tmp_file.name
    finally:
        try:
            if os.path.exists(tmp_file.name):
                os.remove(tmp_file.name)
        except Exception:
            pass
        if len(file_bytes) > 5 * 1024 * 1024:
            gc.collect()



# ---------------------------------------------------------------------------
# 1. Image Ingestion & Orientation Normalization
# ---------------------------------------------------------------------------
def normalize_image(image_source: Any) -> Image.Image:
    """Normalize input image to RGB orientation-corrected PIL Image.
    Converts RGBA and P modes to RGB and applies EXIF transposition.
    """
    img = _prepare_pil_image(image_source)
    if img is None:
        raise ValueError(f"Unsupported or unprocessable image input type: {type(image_source)}")

    try:
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass

    if img.mode in ("RGBA", "P", "LA"):
        rgb_img = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode in ("RGBA", "LA"):
            bands = img.split()
            mask = bands[-1] if len(bands) > 1 else None
            rgb_img.paste(img, mask=mask)
        else:
            rgb_img.paste(img.convert("RGB"))
        img = rgb_img
    elif img.mode != "RGB":
        img = img.convert("RGB")

    return img


def load_image(file_source: Any) -> Image.Image:
    """Load an image from bytes, file path, file buffer, or Streamlit UploadedFile.
    Automatically handles EXIF rotation, format normalization, and converts RGBA/P to RGB.
    """
    return normalize_image(file_source)


# ---------------------------------------------------------------------------
# 2. Metadata & Visual Geometry Extraction
# ---------------------------------------------------------------------------
def format_file_size(size_in_bytes: Optional[int]) -> str:
    """Format bytes into human-readable string (KB, MB)."""
    if size_in_bytes is None:
        return "Unknown size"
    if size_in_bytes < 1024:
        return f"{size_in_bytes} B"
    elif size_in_bytes < 1024 * 1024:
        return f"{size_in_bytes / 1024:.1f} KB"
    else:
        return f"{size_in_bytes / (1024 * 1024):.2f} MB"


def _calculate_aspect_ratio_label(width: int, height: int) -> str:
    """Compute standard or normalized aspect ratio string."""
    if height == 0:
        return "N/A"
    ratio = width / height

    # Match common photographic & screen aspect ratios
    common_ratios = [
        (1.0, "1:1 (Square)"),
        (16 / 9, "16:9 (Widescreen)"),
        (4 / 3, "4:3 (Standard)"),
        (3 / 2, "3:2 (Classic 35mm)"),
        (9 / 16, "9:16 (Vertical / Mobile)"),
        (3 / 4, "3:4 (Portrait)"),
        (2 / 3, "2:3 (Portrait)")
    ]

    for target_ratio, label in common_ratios:
        if abs(ratio - target_ratio) < 0.05:
            return label

    return f"{ratio:.2f}:1"


def extract_image_metadata(
    image: Image.Image,
    file_size_bytes: Optional[int] = None,
    original_filename: Optional[str] = None
) -> Dict[str, Any]:
    """Inspect and return comprehensive technical metadata for the given image."""
    width, height = image.size
    megapixels = round((width * height) / 1_000_000, 2)
    format_name = image.format or ("PNG" if image.mode == "RGBA" else "JPEG")
    aspect_label = _calculate_aspect_ratio_label(width, height)

    # Extract EXIF if available
    exif_clean: Dict[str, Any] = {}
    try:
        raw_exif = image.getexif()
        if raw_exif:
            for tag_id, val in raw_exif.items():
                tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                # Skip long binary/unprintable values
                if isinstance(val, (bytes, bytearray)) and len(val) > 64:
                    continue
                val_str = str(val).strip()
                if val_str and len(val_str) < 100:
                    exif_clean[tag_name] = val_str
    except Exception:
        pass

    # DPI detection
    dpi = image.info.get("dpi")
    dpi_str = f"{dpi[0]} × {dpi[1]}" if dpi and isinstance(dpi, tuple) else "Standard (72-96 DPI)"

    return {
        "filename": original_filename or "Uploaded Image",
        "format": format_name.upper(),
        "mode": image.mode,
        "width": width,
        "height": height,
        "dimensions": f"{width} × {height} px",
        "megapixels": megapixels,
        "aspect_ratio": aspect_label,
        "file_size": format_file_size(file_size_bytes),
        "file_size_formatted": format_file_size(file_size_bytes),
        "dpi": dpi_str,
        "has_transparency": image.mode in ("RGBA", "LA") or "transparency" in image.info,
        "exif": exif_clean
    }


# ---------------------------------------------------------------------------
# 3. Dominant Color Swatch Calculation
# ---------------------------------------------------------------------------
def extract_dominant_colors(
    image: Image.Image,
    num_colors: int = 5
) -> List[Dict[str, Any]]:
    """Extract top dominant colors with RGB, Hex codes, percentages, and contrast flags.

    Returns a list of dicts:
        [{"hex": "#C65D3B", "rgb": (198, 93, 59), "percentage": 38.5, "is_dark": True}, ...]
    """
    # 1. Resize image to small thumbnail for fast, smoothed sampling
    thumb = image.copy()
    thumb.thumbnail((150, 150))

    # 2. Convert to RGB (removing transparency background distortion)
    if thumb.mode in ("RGBA", "P"):
        rgb_thumb = Image.new("RGB", thumb.size, (255, 255, 255))
        if thumb.mode == "RGBA":
            rgb_thumb.paste(thumb, mask=thumb.split()[3])
        else:
            rgb_thumb.paste(thumb.convert("RGB"))
        thumb = rgb_thumb
    elif thumb.mode != "RGB":
        thumb = thumb.convert("RGB")

    # 3. Quantize using median cut
    quantized = thumb.quantize(colors=num_colors, method=Image.Quantize.MEDIANCUT)
    palette = quantized.getpalette()  # List of [R, G, B, R, G, B, ...]
    pixel_counts = Counter(quantized.getdata())
    total_pixels = sum(pixel_counts.values()) or 1

    color_swatches = []
    # Sort palette indexes by pixel frequency descending
    for index, count in pixel_counts.most_common(num_colors):
        r = palette[index * 3]
        g = palette[index * 3 + 1]
        b = palette[index * 3 + 2]
        hex_code = f"#{r:02x}{g:02x}{b:02x}".upper()
        percentage = round((count / total_pixels) * 100, 1)

        # Standard ITU-R BT.601 luminance formula to determine contrast text color
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
        is_dark = luminance < 0.55

        color_swatches.append({
            "hex": hex_code,
            "rgb": (r, g, b),
            "percentage": percentage,
            "is_dark": is_dark,
            "text_color": "#FFFFFF" if is_dark else "#1A1A1A"
        })

    return color_swatches


# ---------------------------------------------------------------------------
# 4. LLM Router Interface for Visual OCR & Analysis
# ---------------------------------------------------------------------------
PRESET_PROMPTS = {
    "ocr": (
        "Please perform high-accuracy Optical Character Recognition (OCR) on this image. "
        "Extract and transcribe all visible text, numbers, headers, and tables exactly as they appear. "
        "Preserve tabular formatting using Markdown tables where applicable. "
        "If there are handwritten notes, stamps, or labels, transcribe them clearly under an 'Annotations' section."
    ),
    "describe": (
        "Provide a comprehensive, professional visual description of this image. "
        "Analyze:\n"
        "1. Overall subject matter and core composition\n"
        "2. Key visual elements, objects, and people\n"
        "3. Aesthetic details (colors, lighting, style, textures)\n"
        "4. Context, setting, and potential intent or message."
    ),
    "document_audit": (
        "Analyze this document/receipt/invoice image as an intelligent document auditor. "
        "Extract:\n"
        "- Document Type (Invoice, Receipt, Contract, Medical Note, etc.)\n"
        "- Issuer / Vendor Name\n"
        "- Date(s) & Reference Numbers\n"
        "- Line Items or Key Statements\n"
        "- Financial Totals, Taxes, or Grand Balances (if applicable)\n"
        "- Potential Anomalies, Discrepancies, or Missing Information."
    ),
    "chart_diagram": (
        "You are a multimodal visual intelligence specialist. Analyze the attached chart, diagram, or UI graphic.\n\n"
        "Provide your output in three distinct sections:\n"
        "1. **Visual Classification**: Type of graphic (bar chart, flowchart, architecture diagram, scan artifact, etc.).\n"
        "2. **Key Data Points & Trends**: Exact values, axis labels, legends, directional trends, and anomalies.\n"
        "3. **Executive Summary**: 2-3 bullet points synthesizing what the visual represents and key takeaways."
    )
}


class VisionAnalysisResult(str):
    """String wrapper containing multimodal output with attached telemetry and image dimensions."""
    telemetry: Dict[str, Any]
    image_dimensions: Tuple[int, int]

    def __new__(
        cls,
        content: str,
        telemetry: Optional[Dict[str, Any]] = None,
        dimensions: Optional[Tuple[int, int]] = None
    ):
        obj = super().__new__(cls, content)
        obj.telemetry = telemetry or {}
        obj.image_dimensions = dimensions or (0, 0)
        return obj

    def __iter__(self):
        yield str(self)
        yield self.telemetry
        yield self.image_dimensions


def analyze_image_with_llm(
    image: Any,
    task_type: str = "ocr",
    custom_prompt: Optional[str] = None,
    model_provider: str = "Google Gemini",
    model_name: str = "gemini-2.5-flash",
    api_key: Optional[str] = None,
    return_tuple: bool = False,
    **kwargs
) -> Union[VisionAnalysisResult, Tuple[str, Dict[str, Any], Tuple[int, int]]]:
    """Hook directly into `LLMRouter.route_vision_request()` to perform multimodal vision tasks.

    Args:
        image: PIL Image, bytes, UploadedFile, or file path.
        task_type: One of ['ocr', 'describe', 'document_audit', 'chart_diagram', 'custom'].
        custom_prompt: User question or custom query.
        model_provider: LLM provider ("Google Gemini", "OpenAI", "Ollama (Local)", etc.).
        model_name: Specific model identifier.
        api_key: API key if required by provider.
        return_tuple: If True, explicitly returns a 3-element tuple (text, telemetry, dimensions).

    Returns:
        VisionAnalysisResult (string subclass containing analysis text, `.telemetry` dict,
        and `.image_dimensions` tuple, which can also be unpacked as a 3-element tuple).
    """
    normalized_img = normalize_image(image)
    dimensions = normalized_img.size

    if task_type == "custom" and custom_prompt:
        final_prompt = custom_prompt
    elif task_type in PRESET_PROMPTS:
        if custom_prompt and custom_prompt.strip():
            final_prompt = f"{PRESET_PROMPTS[task_type]}\n\nAdditional User Request: {custom_prompt.strip()}"
        else:
            final_prompt = PRESET_PROMPTS[task_type]
    else:
        final_prompt = custom_prompt or PRESET_PROMPTS["describe"]

    analysis_text = LLMRouter.route_vision_request(
        prompt=final_prompt,
        provider=model_provider,
        image_data=normalized_img,
        model_name=model_name,
        api_key=api_key,
        **kwargs
    )

    telemetry = get_last_telemetry()

    if return_tuple:
        return analysis_text, telemetry, dimensions

    return VisionAnalysisResult(
        content=analysis_text,
        telemetry=telemetry,
        dimensions=dimensions
    )
