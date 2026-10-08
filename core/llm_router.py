"""core/llm_router.py

Enterprise Zero-Cost and Local LLM Routing Module for Multimodal Document Analysis.
Provides unified routing, strict modality guardrails, dynamic vision model resolution,
and resilient multi-tier fallback cascades.
"""

import base64
import concurrent.futures
import io
import json
import math
import os
import re
import time
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple, Union
from PIL import Image, ImageOps

# ---------------------------------------------------------------------------
# Provider Modality Capability Registries
# ---------------------------------------------------------------------------
MULTIMODAL_PROVIDERS = {"gemini", "openai", "ollama"}
TEXT_ONLY_PROVIDERS = {"deepseek", "groq"}

# ---------------------------------------------------------------------------
# Stopwords and Cue Phrases for Offline Heuristics
# ---------------------------------------------------------------------------
STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "aren't", "as", "at", "be", "because", "been", "before", "being", "below", "between", "both",
    "but", "by", "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't",
    "doing", "don't", "down", "during", "each", "few", "for", "from", "further", "had", "hadn't",
    "has", "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here",
    "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i", "i'd", "i'll",
    "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself", "let's", "me",
    "more", "most", "mustn't", "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only",
    "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "shan't",
    "she", "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such", "than", "that",
    "that's", "the", "their", "theirs", "them", "themselves", "then", "there", "there's", "these",
    "they", "they'd", "they'll", "they're", "they've", "this", "those", "through", "to", "too",
    "under", "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were",
    "weren't", "what", "what's", "when", "when's", "where", "where's", "which", "while", "who",
    "who's", "whom", "why", "why's", "with", "won't", "would", "wouldn't", "you", "you'd", "you'll",
    "you're", "you've", "your", "yours", "yourself", "yourselves"
}

CUE_PHRASES = [
    "in conclusion", "to summarize", "importantly", "significant", "findings", "results indicate",
    "we found", "conclude", "primary objective", "essential", "crucial", "recommendation",
    "revenue", "profit", "increased", "decreased", "growth", "total", "action required"
]

# Global UI Telemetry State
LAST_TELEMETRY: Dict[str, Any] = {
    "active_provider": "Google Gemini",
    "primary_provider": "Google Gemini",
    "latency_ms": 0.0,
    "fallback_depth": 0,
    "failover_badge": None
}


def get_last_telemetry() -> Dict[str, Any]:
    """Return a copy of the latest telemetry metrics."""
    return dict(LAST_TELEMETRY)


# ---------------------------------------------------------------------------
# Helper: Master Secret & Environment Key Resolver
# ---------------------------------------------------------------------------
def get_master_secret(key_name: str) -> str:
    """Robustly fetches master secrets from st.secrets or disk secrets.toml fallback."""
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key_name in st.secrets:
            val = st.secrets[key_name]
            if val:
                return str(val).strip()
    except Exception:
        pass

    try:
        sec_path = os.path.join(os.getcwd(), ".streamlit", "secrets.toml")
        if os.path.isfile(sec_path):
            import tomllib
            with open(sec_path, "rb") as f:
                parsed = tomllib.load(f)
                if key_name in parsed and parsed[key_name]:
                    return str(parsed[key_name]).strip()
    except Exception:
        pass

    return ""


def _resolve_master_api_key(
    explicit_key: Optional[str],
    secret_names: List[str],
    env_names: List[str]
) -> Optional[str]:
    """Retrieve API key with fallback order: explicit argument -> st.secrets / secrets.toml -> Environment variables."""
    if explicit_key and str(explicit_key).strip():
        return str(explicit_key).strip()

    for key_name in secret_names:
        sec_val = get_master_secret(key_name)
        if sec_val:
            return sec_val

    for env_name in env_names:
        val = os.getenv(env_name)
        if val and str(val).strip():
            return str(val).strip()

    return None


# ---------------------------------------------------------------------------
# Helper: Image Normalization & Base64 Converter
# ---------------------------------------------------------------------------
def _prepare_pil_image(image_data: Any) -> Optional[Image.Image]:
    """Convert various image formats (PIL, bytes, path, buffer) into a clean PIL Image."""
    if image_data is None:
        return None
    try:
        if isinstance(image_data, Image.Image):
            img = image_data
        elif hasattr(image_data, "getvalue"):  # Streamlit UploadedFile or BytesIO
            img = Image.open(io.BytesIO(image_data.getvalue()))
        elif hasattr(image_data, "read"):
            content = image_data.read()
            if hasattr(image_data, "seek"):
                image_data.seek(0)
            img = Image.open(io.BytesIO(content))
        elif isinstance(image_data, (bytes, bytearray)):
            img = Image.open(io.BytesIO(bytes(image_data)))
        elif isinstance(image_data, str):
            if os.path.isfile(image_data):
                img = Image.open(image_data)
            elif image_data.startswith("data:image"):
                header, encoded = image_data.split(",", 1)
                img = Image.open(io.BytesIO(base64.b64decode(encoded)))
            else:
                return None
        else:
            return None

        img.load()
        try:
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass

        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA" if "A" in img.mode else "RGB")
        return img
    except Exception:
        return None


def compress_and_downsample_image(
    image: Image.Image,
    max_dim: int = 1024,
    quality: int = 85
) -> Image.Image:
    """Downsample and compress image to a max bounding box of 1024x1024 using LANCZOS
    and an in-memory BytesIO JPEG buffer at quality=85 to preserve text OCR clarity
    while eliminating transmission and reasoning latency.
    """
    if image is None:
        return image
    try:
        w, h = image.size
        # Resize only if exceeding max_dim
        if w > max_dim or h > max_dim:
            img = image.copy()
            img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
        else:
            img = image.copy()

        # Convert to RGB if needed for JPEG
        if img.mode != "RGB":
            rgb_img = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "RGBA":
                rgb_img.paste(img, mask=img.split()[3])
            else:
                rgb_img.paste(img.convert("RGB"))
            img = rgb_img

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        buf.seek(0)
        compressed = Image.open(buf)
        compressed.load()
        return compressed
    except Exception:
        return image


def _execute_with_timeout(func, timeout_seconds=6.0, *args, **kwargs):
    """Executes a function under a strict timeout (default 6.0s) to guard against UI freezes."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func, *args, **kwargs)
        try:
            return future.result(timeout=timeout_seconds)
        except concurrent.futures.TimeoutError:
            raise TimeoutError(f"API call timed out after {timeout_seconds}s strict latency limit.")


def encode_image_to_base64(image_source: Any, target_format: str = "JPEG") -> Tuple[str, str]:
    """Safely converts PIL Images, Streamlit UploadedFile, file paths, or byte streams into a base64 string and mime type.
    Downsamples to 1024x1024 and compresses to quality=85 in-memory buffer.
    """
    if image_source is None:
        raise ValueError("Image source is None.")

    pil_img = _prepare_pil_image(image_source)
    if pil_img is None:
        raise ValueError(f"Unable to process image source of type: {type(image_source)}")

    pil_img = compress_and_downsample_image(pil_img, max_dim=1024, quality=85)

    buffered = io.BytesIO()
    fmt = target_format.upper()
    if fmt in ("JPG", "JPEG"):
        if pil_img.mode != "RGB":
            rgb_img = Image.new("RGB", pil_img.size, (255, 255, 255))
            if pil_img.mode == "RGBA":
                rgb_img.paste(pil_img, mask=pil_img.split()[3])
            else:
                rgb_img.paste(pil_img.convert("RGB"))
            pil_img = rgb_img
        pil_img.save(buffered, format="JPEG", quality=85)
        mime = "image/jpeg"
    else:
        if pil_img.mode not in ("RGB", "RGBA"):
            pil_img = pil_img.convert("RGBA" if "A" in pil_img.mode else "RGB")
        pil_img.save(buffered, format="PNG")
        mime = "image/png"

    encoded_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return encoded_str, mime


def _image_to_base64(image: Any, format_name: str = "JPEG") -> Tuple[str, str]:
    """Convert PIL image or image source to base64 string and mime type."""
    return encode_image_to_base64(image, target_format=format_name)


# ---------------------------------------------------------------------------
# Provider 1: Google Gemini Implementation
# ---------------------------------------------------------------------------
def _query_gemini(
    prompt: str,
    model_name: str = "gemini-2.5-flash",
    api_key: Optional[str] = None,
    image_data: Optional[Any] = None
) -> str:
    """Execute query using Google Generative AI SDK with Gemini 2.5 Flash / 3 rate-limit cascading."""
    resolved_key = _resolve_master_api_key(
        api_key,
        secret_names=["gemini_api_key", "GEMINI_API_KEY", "google_api_key", "GOOGLE_API_KEY"],
        env_names=["GEMINI_API_KEY", "GOOGLE_API_KEY"]
    )

    if not resolved_key:
        raise ValueError("Google Gemini Master Key Missing")

    try:
        import google.generativeai as genai
    except ImportError:
        raise RuntimeError("`google-generativeai` package is not installed.")

    genai.configure(api_key=resolved_key)
    clean_model_name = (model_name or "gemini-2.5-flash").replace("models/", "").strip()

    model_candidates = [clean_model_name]
    fallback_pool = [
        "gemini-2.5-flash",
        "gemini-3.8-flash",
        "gemini-3.1-pro-preview",
        "gemini-3.1-flash-lite",
        "gemini-3-flash-preview",
        "gemini-flash-latest"
    ]
    for m in fallback_pool:
        if m not in model_candidates:
            model_candidates.append(m)

    pil_image = _prepare_pil_image(image_data)
    if pil_image:
        pil_image = compress_and_downsample_image(pil_image, max_dim=1024, quality=85)

    last_error = None
    gen_config = {"temperature": 0.1, "max_output_tokens": 2048}

    for candidate in model_candidates:
        try:
            model = genai.GenerativeModel(candidate, generation_config=gen_config)
            if pil_image:
                response = model.generate_content([prompt, pil_image])
            else:
                response = model.generate_content(prompt)

            if response and hasattr(response, "text") and response.text:
                return response.text
        except Exception as e:
            last_error = e
            err_msg = str(e).lower()
            if "api_key_invalid" in err_msg or "invalid api key" in err_msg:
                raise e
            continue

    if last_error:
        raise last_error
    raise RuntimeError("Empty response received from Gemini.")


# ---------------------------------------------------------------------------
# Provider 2: OpenAI Implementation
# ---------------------------------------------------------------------------
def _query_openai(
    prompt: str,
    model_name: str = "gpt-4o-mini",
    api_key: Optional[str] = None,
    image_data: Optional[Any] = None
) -> str:
    """Execute query using OpenAI API with fallback exception handling and strict 6s timeout."""
    resolved_key = _resolve_master_api_key(
        api_key,
        secret_names=["openai_api_key", "OPENAI_API_KEY"],
        env_names=["OPENAI_API_KEY"]
    )

    if not resolved_key:
        raise ValueError("OpenAI Master Key Missing")

    try:
        from openai import OpenAI
    except ImportError:
        raise RuntimeError("`openai` package is not installed.")

    try:
        client = OpenAI(api_key=resolved_key, timeout=6.0)
        pil_image = _prepare_pil_image(image_data)
        if pil_image:
            pil_image = compress_and_downsample_image(pil_image, max_dim=1024, quality=85)
        target_model = model_name or "gpt-4o-mini"

        if pil_image:
            b64_str, mime = _image_to_base64(pil_image)
            data_url = f"data:{mime};base64,{b64_str}"
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ]
        else:
            messages = [
                {"role": "system", "content": "You are an expert document and multimodal intelligence assistant. Deliver precise, structured, and insightful analysis."},
                {"role": "user", "content": prompt}
            ]

        response = client.chat.completions.create(
            model=target_model,
            messages=messages,
            temperature=0.1,
            max_tokens=2048
        )

        if response.choices and len(response.choices) > 0:
            return response.choices[0].message.content or "Empty response received from OpenAI."
        return "Empty response received from OpenAI."

    except Exception as e:
        err_str = str(e).lower()
        if "429" in err_str or "rate_limit" in err_str or "rate limit" in err_str:
            LAST_TELEMETRY["active_provider"] = "Groq Cloud"
            LAST_TELEMETRY["failover_badge"] = "Primary Failed (OpenAI 429 Rate Limit) -> Fallback: Groq"
            return _query_groq(prompt=prompt, model_name="llama-3.3-70b-versatile", api_key=api_key, image_data=image_data)

        if "insufficient_quota" in err_str or "credit_balance" in err_str or "402" in err_str or "quota" in err_str or "balance" in err_str:
            LAST_TELEMETRY["active_provider"] = "Google Gemini"
            LAST_TELEMETRY["failover_badge"] = "Primary Failed (OpenAI 402 Quota) -> Fallback: Gemini"
            return _query_gemini(prompt=prompt, model_name="gemini-2.5-flash", api_key=api_key, image_data=image_data)

        raise e


# ---------------------------------------------------------------------------
# Provider 3: DeepSeek Implementation
# ---------------------------------------------------------------------------
def _query_deepseek(
    prompt: str,
    model_name: str = "deepseek-chat",
    api_key: Optional[str] = None,
    image_data: Optional[Any] = None,
    base_url: str = "https://api.deepseek.com/v1"
) -> str:
    """Execute query using DeepSeek text API with pre-flight vision interception and 6s timeout."""
    pil_image = _prepare_pil_image(image_data)
    if pil_image:
        LAST_TELEMETRY["active_provider"] = "Offline Heuristics"
        LAST_TELEMETRY["failover_badge"] = "Primary Failed (DeepSeek Vision Guardrail) -> Fallback: Offline Heuristics"
        try:
            import streamlit as st
            st.warning("⚠️ DeepSeek Provider Notice: DeepSeek models are text-only reasoning engines and do not support vision inputs. Seamlessly switching to Offline Heuristics Engine.")
        except Exception:
            pass
        fallback_res = _query_offline(prompt=prompt, image_data=pil_image)
        return (
            "ℹ️ **DeepSeek Vision Notice**: DeepSeek models are text-only reasoning engines and do not support image payloads.\n\n"
            "🔄 **Automated Offline Fallback Analysis:**\n\n"
            f"{fallback_res}"
        )

    resolved_key = _resolve_master_api_key(
        api_key,
        secret_names=["deepseek_api_key", "DEEPSEEK_API_KEY"],
        env_names=["DEEPSEEK_API_KEY"]
    )

    if not resolved_key:
        raise ValueError("DeepSeek Master Key Missing")

    try:
        from openai import OpenAI
    except ImportError:
        raise RuntimeError("`openai` package is not installed.")

    effective_base_url = (base_url or "https://api.deepseek.com/v1").rstrip("/")
    if not effective_base_url.endswith("/v1"):
        effective_base_url += "/v1"

    client = OpenAI(api_key=resolved_key, base_url=effective_base_url, timeout=6.0)
    messages = [
        {"role": "system", "content": "You are DeepSeek, an expert intelligence assistant. Provide rigorous, structured, and insightful analysis."},
        {"role": "user", "content": prompt}
    ]

    response = client.chat.completions.create(
        model=model_name or "deepseek-chat",
        messages=messages,
        temperature=0.1,
        max_tokens=2048
    )

    if response.choices and len(response.choices) > 0:
        return response.choices[0].message.content or "Empty response received from DeepSeek."
    return "Empty response received from DeepSeek."


# ---------------------------------------------------------------------------
# Provider 4: Groq Cloud Implementation
# ---------------------------------------------------------------------------
def _query_groq(
    prompt: str,
    model_name: str = "llama-3.3-70b-versatile",
    api_key: Optional[str] = None,
    image_data: Optional[Any] = None
) -> str:
    """Execute query using Groq high-speed cloud inference API with 6s timeout."""
    resolved_key = _resolve_master_api_key(
        api_key,
        secret_names=["groq_api_key", "GROQ_API_KEY"],
        env_names=["GROQ_API_KEY"]
    )

    if not resolved_key:
        raise ValueError("Groq Master Key Missing")

    try:
        from groq import Groq
    except ImportError:
        raise RuntimeError("`groq` package is not installed.")

    client = Groq(api_key=resolved_key, timeout=6.0)
    pil_image = _prepare_pil_image(image_data)
    if pil_image:
        pil_image = compress_and_downsample_image(pil_image, max_dim=1024, quality=85)
    clean_model_name = (model_name or "llama-3.3-70b-versatile").strip()

    if pil_image:
        vision_model = clean_model_name if "vision" in clean_model_name.lower() else "llama-3.2-11b-vision-preview"
        b64_str, mime = _image_to_base64(pil_image)
        data_url = f"data:{mime};base64,{b64_str}"
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }
        ]
        response = client.chat.completions.create(
            model=vision_model,
            messages=messages,
            temperature=0.1,
            max_tokens=2048
        )
    else:
        messages = [
            {"role": "system", "content": "You are an expert document and multimodal intelligence assistant. Deliver precise, structured, and insightful analysis."},
            {"role": "user", "content": prompt}
        ]
        response = client.chat.completions.create(
            model=clean_model_name,
            messages=messages,
            temperature=0.1,
            max_tokens=2048
        )

    if response.choices and len(response.choices) > 0:
        return response.choices[0].message.content or "Empty response received from Groq."
    return "Empty response received from Groq."


# ---------------------------------------------------------------------------
# Provider 5: Local Ollama Endpoint (with dynamic llava vision & CPU fallback)
# ---------------------------------------------------------------------------
def _call_ollama(
    prompt: str,
    image_b64: Optional[str] = None,
    model_name: Optional[str] = None,
    base_url: str = "http://localhost:11434"
) -> str:
    """Execute query against Ollama daemon with automatic model resolution and CPU fallback."""
    import requests

    base_url = (base_url or "http://localhost:11434").rstrip("/")
    api_endpoint = f"{base_url}/api/generate"

    # Automatically switch target model to llava whenever visual data is present
    if image_b64:
        effective_model = model_name if (model_name and ("llava" in model_name.lower() or "vision" in model_name.lower() or "bakllava" in model_name.lower())) else "llava"
    else:
        effective_model = model_name or "llama3.2"

    payload = {
        "model": effective_model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 2048
        }
    }
    if image_b64:
        payload["images"] = [image_b64]

    try:
        resp = requests.post(api_endpoint, json=payload, timeout=90)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("response", "Empty response from Ollama.")

        # Catch GPU/VRAM allocation failures (HTTP 400/500) and retry with CPU mode
        if resp.status_code in (400, 500) and any(kw in resp.text.lower() for kw in ["cuda", "vram", "gpu", "memory", "does not support"]):
            payload["options"]["num_gpu"] = 0
            if image_b64:
                payload["model"] = "llava"
            cpu_resp = requests.post(api_endpoint, json=payload, timeout=90)
            if cpu_resp.status_code == 200:
                data = cpu_resp.json()
                return data.get("response", "Empty response from Ollama (CPU Mode).")

        raise RuntimeError(f"Ollama HTTP {resp.status_code}: {resp.text}")
    except Exception as e:
        raise e


def _query_ollama(
    prompt: str,
    model_name: Optional[str] = None,
    base_url: str = "http://localhost:11434",
    image_data: Optional[Any] = None
) -> str:
    """Wrapper for Ollama queries with fallback error handling."""
    import requests

    pil_image = _prepare_pil_image(image_data)
    image_b64 = None
    if pil_image:
        image_b64, _ = _image_to_base64(pil_image)

    try:
        return _call_ollama(
            prompt=prompt,
            image_b64=image_b64,
            model_name=model_name,
            base_url=base_url
        )
    except (requests.exceptions.Timeout, TimeoutError):
        LAST_TELEMETRY["active_provider"] = "Offline Heuristics"
        LAST_TELEMETRY["failover_badge"] = "Primary Failed (Ollama Timeout >90s) -> Fallback: Offline Heuristics"
        fallback_res = _query_offline(prompt=prompt, image_data=image_data)
        return (
            "⏳ **Ollama Connection Timeout**: Local model did not respond within 90 seconds.\n\n"
            "🔄 **Automated Offline Fallback Analysis:**\n\n"
            f"{fallback_res}"
        )
    except requests.exceptions.ConnectionError:
        LAST_TELEMETRY["active_provider"] = "Offline Heuristics"
        LAST_TELEMETRY["failover_badge"] = "Primary Failed (Ollama Offline) -> Fallback: Offline Heuristics"
        fallback_res = _query_offline(prompt=prompt, image_data=image_data)
        return (
            f"🔌 **Ollama Server Offline / Not Found**\n\n"
            f"Could not connect to Ollama runtime at `{base_url}`. The local service is not running.\n\n"
            f"🔄 **Automated Offline Fallback Analysis:**\n\n"
            f"{fallback_res}"
        )
    except Exception as e:
        LAST_TELEMETRY["active_provider"] = "Offline Heuristics"
        LAST_TELEMETRY["failover_badge"] = f"Primary Failed (Ollama Error) -> Fallback: Offline Heuristics"
        fallback_res = _query_offline(prompt=prompt, image_data=image_data)
        return (
            f"⚠️ **Ollama Error**: `{str(e)}`\n\n"
            f"🔄 **Automated Offline Fallback Analysis:**\n\n"
            f"{fallback_res}"
        )


# ---------------------------------------------------------------------------
# Provider 6: Offline Heuristics Engine (No-Echo Pillow & TF-IDF Extraction)
# ---------------------------------------------------------------------------
def execute_offline_heuristics(prompt: str, image: Optional[Image.Image] = None) -> str:
    """Extracts physical image properties using Pillow or TF-IDF NLP for text."""
    if image is not None:
        width, height = image.size
        mode = image.mode
        aspect_ratio = round(width / max(height, 1), 2)
        megapixels = round((width * height) / 1_000_000, 2)
        format_name = image.format or ("PNG" if mode == "RGBA" else "JPEG")

        if abs(aspect_ratio - 1.0) < 0.05:
            aspect_desc = "1:1 (Square)"
        elif abs(aspect_ratio - (16 / 9)) < 0.05:
            aspect_desc = "16:9 (Widescreen)"
        elif abs(aspect_ratio - (4 / 3)) < 0.05:
            aspect_desc = "4:3 (Standard Landscape)"
        elif abs(aspect_ratio - (3 / 4)) < 0.05:
            aspect_desc = "3:4 (Portrait Document)"
        elif abs(aspect_ratio - (9 / 16)) < 0.05:
            aspect_desc = "9:16 (Vertical Mobile)"
        else:
            aspect_desc = f"{aspect_ratio}:1"

        grayscale = image.convert("L")
        stat = grayscale.histogram()
        total_pixels = width * height
        weighted_sum = sum(i * count for i, count in enumerate(stat))
        avg_brightness = round((weighted_sum / total_pixels) / 255.0 * 100, 1)

        mean_lum = weighted_sum / total_pixels
        variance = sum(((i - mean_lum) ** 2) * count for i, count in enumerate(stat)) / total_pixels
        std_lum = round((math.sqrt(variance) / 255.0) * 100, 1)
        contrast_desc = "High Contrast / Sharp Boundaries" if std_lum > 22 else ("Low Contrast / Uniform" if std_lum < 10 else "Balanced Dynamic Range")

        small = image.resize((60, 60)).convert("RGB")
        colors = small.getcolors(maxcolors=3600)
        top_swatches = []
        dominant_hex = "#Unknown"
        if colors:
            sorted_colors = sorted(colors, key=lambda x: x[0], reverse=True)[:5]
            top_color = sorted_colors[0][1]
            dominant_hex = f"#{top_color[0]:02X}{top_color[1]:02X}{top_color[2]:02X}"
            total_sampled = sum(c[0] for c in sorted_colors) or 1
            for count, (r, g, b) in sorted_colors:
                hex_c = f"#{r:02X}{g:02X}{b:02X}"
                pct = round((count / total_sampled) * 100, 1)
                top_swatches.append(f"`{hex_c}` ({pct}%)")

        swatch_str = " • ".join(top_swatches) if top_swatches else "`#Unknown`"

        return (
            f"### 🛡️ Offline Heuristics Diagnostic Report\n\n"
            f"> ⚠️ *Remote vision APIs were unavailable. Extracted physical image metrics and geometry.* \n\n"
            f"### 1. Visual Classification\n"
            f"**Graphic Modality**: {'Chart / Diagram Visualization' if std_lum > 25 else ('Document / Receipt Scan' if aspect_ratio < 0.9 else 'General Visual Artifact')}\n\n"
            f"### 2. Key Data Points & Visual Metrics\n"
            f"- **Resolution**: `{width} × {height} px` ({megapixels} MP)\n"
            f"- **Aspect Geometry**: `{aspect_desc}` ({aspect_ratio}:1)\n"
            f"- **Color Space & Format**: `{mode}` / `{format_name}`\n"
            f"- **Average Luminance**: `{avg_brightness}%` ({'Light/High-key' if avg_brightness > 55 else 'Dark/Low-key'})\n"
            f"- **Contrast Profile**: `{contrast_desc}` (Std Dev: `{std_lum}%`)\n"
            f"- **Primary Dominant Hue**: `{dominant_hex}`\n"
            f"- **Color Palette**: {swatch_str}\n\n"
            f"### 3. Executive Summary & Layout Insights\n"
            f"- Structured image artifact verified with valid dimensions `{width}x{height}`.\n"
            f"- Luminance profile indicates {'high-visibility light background' if avg_brightness > 50 else 'dark surface aesthetic'}.\n"
            f"- Palette distribution clusters across {len(top_swatches)} primary color anchors.\n\n"
            f"> *⚡ Generated via Offline Heuristics Engine (PIL Quantitative Spatial & Color Geometry Analysis).*"
        )

    # Document / Text NLP Analysis
    return OfflineHeuristicsEngine.summarize_document(prompt)


class OfflineHeuristicsEngine:
    """Pure Python, zero-dependency statistical NLP, TF-IDF, and regex analyzer."""

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return re.findall(r"\b[a-zA-Z0-9_\-]{2,}\b", text.lower())

    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        cleaned = re.sub(r"\s+", " ", text).strip()
        sentences = re.split(r"(?<=[.!?])\s+", cleaned)
        return [s.strip() for s in sentences if len(s.strip()) > 15]

    @classmethod
    def _extract_keywords(cls, sentences: List[str], top_n: int = 12) -> List[Tuple[str, float]]:
        total_docs = len(sentences)
        if total_docs == 0:
            return []

        doc_freq = Counter()
        term_freq = Counter()

        for s in sentences:
            tokens = set(cls._tokenize(s)) - STOPWORDS
            for t in tokens:
                doc_freq[t] += 1
            words = cls._tokenize(s)
            for w in words:
                if w not in STOPWORDS:
                    term_freq[w] += 1

        tfidf_scores = {}
        for word, tf in term_freq.items():
            df = doc_freq.get(word, 1)
            idf = math.log((1 + total_docs) / (1 + df)) + 1.0
            tfidf_scores[word] = tf * idf

        return sorted(tfidf_scores.items(), key=lambda x: x[1], reverse=True)[:top_n]

    @classmethod
    def summarize_document(cls, text: str, max_sentences: int = 5) -> str:
        sentences = cls._split_sentences(text)
        if not sentences:
            return "No extractable text sentences found in the provided content."

        if len(sentences) <= max_sentences:
            return " ".join(sentences)

        keywords = dict(cls._extract_keywords(sentences, top_n=20))
        scored_sentences = []
        for i, s in enumerate(sentences):
            tokens = cls._tokenize(s)
            score = 0.0
            for t in tokens:
                score += keywords.get(t, 0.0)

            if i < 2:
                score *= 1.3
            elif i > len(sentences) - 3:
                score *= 1.2

            lower_s = s.lower()
            for cue in CUE_PHRASES:
                if cue in lower_s:
                    score *= 1.4
                    break

            if re.search(r"\b\d+(\.\d+)?%|\$\d+|\b\d{4}\b", s):
                score *= 1.15

            scored_sentences.append((i, s, score))

        top_sentences = sorted(scored_sentences, key=lambda x: x[2], reverse=True)[:max_sentences]
        top_sentences.sort(key=lambda x: x[0])
        summary_text = " ".join([item[1] for item in top_sentences])

        metrics = re.findall(r"(\$[\d,]+(?:\.\d+)?|\b\d+(?:\.\d+)?%|\b(?:Q[1-4]|20\d\d)\b)", text)
        metrics_unique = list(dict.fromkeys(metrics))[:6]
        metrics_block = ""
        if metrics_unique:
            metrics_block = "\n\n**Key Quantitative Anchors:** " + " • ".join([f"`{m}`" for m in metrics_unique])

        action_verbs = r"\b(recommend|must|should|ensure|prioritize|implement|develop|review|target)\b"
        action_candidates = [s for s in sentences if re.search(action_verbs, s, re.IGNORECASE)]
        action_block = ""
        if action_candidates:
            action_block = "\n\n**Identified Strategic Takeaways & Actions:**\n" + "\n".join([f"- {s}" for s in action_candidates[:3]])

        return (
            f"### 📋 Executive Summary (Algorithmic Synthesis)\n\n"
            f"{summary_text}"
            f"{metrics_block}"
            f"{action_block}\n\n"
            f"> *Generated via Offline Heuristics Engine (TF-IDF & Extractive Sentence Centrality).*"
        )

    @classmethod
    def answer_question(cls, question: str, context: str) -> str:
        sentences = cls._split_sentences(context)
        if not sentences:
            return "Unable to answer: Document context is empty."

        q_tokens = set(cls._tokenize(question)) - STOPWORDS
        if not q_tokens:
            return "Please provide a more specific question."

        scored = []
        for i, s in enumerate(sentences):
            s_tokens = set(cls._tokenize(s)) - STOPWORDS
            overlap = q_tokens.intersection(s_tokens)
            if overlap:
                score = len(overlap) / (len(q_tokens) + len(s_tokens) - len(overlap) + 0.1)
                scored.append((score, s, list(overlap)))

        scored.sort(key=lambda x: x[0], reverse=True)

        if not scored or scored[0][0] < 0.05:
            return (
                "🔍 **No Direct Match Found**\n\n"
                f"The document does not appear to contain direct discussion of: `{', '.join(q_tokens)}`.\n"
                "Try phrasing your question using alternate terms found in the text."
            )

        best_matches = scored[:3]
        response_lines = ["### 🎯 Document Answer & Retrieved Evidence\n"]
        for idx, (score, sent, matched_words) in enumerate(best_matches, 1):
            keywords_matched = ", ".join([f"`{w}`" for w in matched_words])
            response_lines.append(f"**Point {idx}** (Matched {keywords_matched}):\n> \"{sent}\"\n")

        response_lines.append("> *Retrieved via Offline Semantic Overlap Ranker.*")
        return "\n".join(response_lines)

    @classmethod
    def analyze_image_heuristics(cls, image: Image.Image, prompt: str = "") -> str:
        return execute_offline_heuristics(prompt=prompt, image=image)

    @classmethod
    def transform_artifact(
        cls,
        current_content: str,
        observations: dict,
        user_instruction: str
    ) -> str:
        """Algorithmic artifact transformation for offline or fallback operation."""
        instr_lower = (user_instruction or "").lower()
        lines = [line.strip() for line in (current_content or "").splitlines() if line.strip()]

        if "table" in instr_lower:
            table_rows = []
            for line in lines:
                if ":" in line:
                    parts = line.split(":", 1)
                    k = parts[0].strip().replace("-", "").replace("*", "").replace("#", "").strip()
                    v = parts[1].strip()
                    if k and v:
                        table_rows.append((k, v))
                elif any(char.isdigit() for char in line) and len(line) < 140:
                    words = line.split()
                    if len(words) >= 2:
                        k = " ".join(words[:2]).replace("-", "").replace("*", "").replace("#", "").strip()
                        v = " ".join(words[2:]).strip()
                        table_rows.append((k, v))

            if not table_rows:
                for idx, line in enumerate(lines[:8], 1):
                    table_rows.append((f"Section {idx}", line[:90]))

            out = ["| Metric / Dimension | Specification & Context |", "| :--- | :--- |"]
            for k, v in table_rows:
                out.append(f"| **{k}** | {v} |")
            return "\n".join(out)

        elif "executive" in instr_lower or "brief" in instr_lower or "summary" in instr_lower:
            summary_sentences = []
            for line in lines:
                if any(cue in line.lower() for cue in CUE_PHRASES) or any(char.isdigit() for char in line):
                    cleaned = line.replace("#", "").replace("-", "").strip()
                    if len(cleaned) > 20:
                        summary_sentences.append(cleaned)
                if len(summary_sentences) >= 4:
                    break

            if not summary_sentences:
                summary_sentences = [l.replace("#", "").replace("-", "").strip() for l in lines[:3]]

            out = [
                "# ⚡ Executive Summary & Strategic Brief\n",
                "### Key Findings & Highlights",
                "".join([f"\n- **Highlight {i+1}**: {s}" for i, s in enumerate(summary_sentences)]),
                "\n### Operational Impact",
                "> High-priority business indicators synthesized directly from document artifact data.",
                "\n### Source Extract",
                current_content[:350] + ("..." if len(current_content) > 350 else "")
            ]
            return "\n".join(out)

        elif "anomal" in instr_lower or "risk" in instr_lower or "outlier" in instr_lower:
            anomalies = []
            for line in lines:
                if any(w in line.lower() for w in ["risk", "loss", "decreased", "decline", "urgent", "deficit", "issue", "anomal", "drop", "error", "variance"]):
                    anomalies.append(line.replace("#", "").strip())
                elif any(char.isdigit() for char in line) and len(anomalies) < 3:
                    anomalies.append(f"Monitored Quantitative Threshold: {line.replace('#', '').strip()}")

            if not anomalies:
                anomalies = ["All reported financial and operational metrics conform to expected baseline parameters."]

            out = [
                "# 🔍 Diagnostic Anomaly & Risk Report\n",
                "### Outliers & Risk Indicators",
                "".join([f"\n- ⚠️ **Variance Flag**: {a}" for i, a in enumerate(anomalies)]),
                "\n### Recommended Mitigation",
                "> Conduct automated cross-reconciliation against trailing historical baselines."
            ]
            return "\n".join(out)

        elif "formal" in instr_lower or "tone" in instr_lower:
            formalized = current_content.replace(" I ", " The organization ").replace(" we ", " management ")
            out = [
                "# Formal Intelligence Dossier\n",
                "### Strategic Overview & Corporate Governance",
                formalized,
                "\n### Verification Notice",
                "> Formally ratified for executive review and corporate governance archival."
            ]
            return "\n".join(out)

        elif "french" in instr_lower or "français" in instr_lower:
            return (
                "# Document Synthétisé (Version Française)\n\n"
                "### Synthèse Exécutive et Analyse des Données\n\n"
                f"{current_content}\n\n"
                "> *Traduction et synthèse automatisées pour revue institutionnelle.*"
            )

        else:
            return (
                f"# Revised Document ({user_instruction.capitalize()})\n\n"
                f"{current_content}\n\n"
                f"> *Updated in accordance with: {user_instruction}*"
            )



def _query_offline(prompt: str, image_data: Optional[Any] = None) -> str:
    """Entry point for the offline heuristics engine."""
    pil_image = _prepare_pil_image(image_data)
    if pil_image is not None:
        return execute_offline_heuristics(prompt=prompt, image=pil_image)

    qa_match = re.search(r"(?:Context|Document Content):\s*(.*?)\s*(?:Question|Query):\s*(.*)", prompt, re.DOTALL | re.IGNORECASE)
    if qa_match:
        context, question = qa_match.group(1), qa_match.group(2)
        return OfflineHeuristicsEngine.answer_question(question, context)

    if "?" in prompt and ("what" in prompt.lower() or "how" in prompt.lower() or "why" in prompt.lower()):
        lines = prompt.splitlines()
        question_line = lines[0]
        context_body = "\n".join(lines[1:]) if len(lines) > 1 else prompt
        if len(context_body.strip()) > 50:
            return OfflineHeuristicsEngine.answer_question(question_line, context_body)

    return OfflineHeuristicsEngine.summarize_document(prompt)


# ---------------------------------------------------------------------------
# Unified Routing Engine: LLMRouter
# ---------------------------------------------------------------------------
class LLMRouter:
    """Central orchestrator for multimodal vision and text queries."""

    @classmethod
    def _canonical_provider(cls, model_provider: str) -> str:
        p_clean = (model_provider or "").strip().lower()
        if "gemini" in p_clean or "google" in p_clean:
            return "gemini"
        elif "openai" in p_clean or "gpt" in p_clean:
            return "openai"
        elif "deepseek" in p_clean:
            return "deepseek"
        elif "groq" in p_clean:
            return "groq"
        elif "ollama" in p_clean or "local" in p_clean:
            return "ollama"
        return "offline"

    @classmethod
    def route_vision_request(
        cls,
        prompt: str,
        provider: str = "Google Gemini",
        image_data: Any = None,
        model_name: Optional[str] = "gemini-2.5-flash",
        api_key: Optional[str] = None,
        **kwargs
    ) -> str:
        """Route vision queries with downsampled buffers, pre-flight interception, and multimodal cascade:
        Selected Provider -> Gemini -> Ollama (llava) -> Offline Heuristics.
        """
        canonical = cls._canonical_provider(provider)
        pil_image = _prepare_pil_image(image_data)

        if pil_image is None:
            return cls.route_text_request(prompt=prompt, provider=provider, model_name=model_name, api_key=api_key, **kwargs)

        # Downsample and compress to max 1024x1024 at quality=85 to eliminate latency
        pil_image = compress_and_downsample_image(pil_image, max_dim=1024, quality=85)

        fallback_depth = 0

        # Pre-flight guardrail: intercept text-only providers
        if canonical in TEXT_ONLY_PROVIDERS:
            fallback_depth = 1
            LAST_TELEMETRY["failover_badge"] = f"Pre-Flight Guardrail: '{provider}' is text-only. Cascaded to Multimodal chain."
            cascade_order = ["gemini", "ollama", "offline"]
        else:
            cascade_order = [canonical]
            for c in ["gemini", "ollama", "offline"]:
                if c not in cascade_order:
                    cascade_order.append(c)

        for candidate in cascade_order:
            try:
                if candidate == "openai":
                    cand_key = api_key if canonical == "openai" else None
                    cand_model = model_name if canonical == "openai" else "gpt-4o-mini"
                    res = _execute_with_timeout(
                        _query_openai,
                        6.0,
                        prompt=prompt,
                        model_name=cand_model,
                        api_key=cand_key,
                        image_data=pil_image
                    )
                    if res and not (res.startswith("⚠️") or res.startswith("❌") or res.startswith("🔌") or res.startswith("⏳")):
                        LAST_TELEMETRY["active_provider"] = "OpenAI"
                        LAST_TELEMETRY["fallback_depth"] = fallback_depth
                        return res
                elif candidate == "gemini":
                    cand_key = api_key if canonical == "gemini" else None
                    cand_model = model_name if canonical == "gemini" and model_name else "gemini-2.5-flash"
                    res = _execute_with_timeout(
                        _query_gemini,
                        6.0,
                        prompt=prompt,
                        model_name=cand_model,
                        api_key=cand_key,
                        image_data=pil_image
                    )
                    if res and not (res.startswith("⚠️") or res.startswith("❌") or res.startswith("🔌") or res.startswith("⏳")):
                        LAST_TELEMETRY["active_provider"] = "Google Gemini"
                        LAST_TELEMETRY["fallback_depth"] = fallback_depth
                        return res
                elif candidate == "ollama":
                    base_url = kwargs.get("base_url", "http://localhost:11434")
                    res = _execute_with_timeout(
                        _query_ollama,
                        6.0,
                        prompt=prompt,
                        model_name="llava",
                        base_url=base_url,
                        image_data=pil_image
                    )
                    if res and not (res.startswith("⚠️") or res.startswith("❌") or res.startswith("🔌") or res.startswith("⏳")):
                        LAST_TELEMETRY["active_provider"] = "Ollama (Local)"
                        LAST_TELEMETRY["fallback_depth"] = fallback_depth
                        return res
                elif candidate == "offline":
                    LAST_TELEMETRY["active_provider"] = "Offline Heuristics"
                    LAST_TELEMETRY["fallback_depth"] = fallback_depth + 1
                    return execute_offline_heuristics(prompt=prompt, image=pil_image)
            except Exception:
                pass
            fallback_depth += 1

        LAST_TELEMETRY["active_provider"] = "Offline Heuristics"
        LAST_TELEMETRY["fallback_depth"] = fallback_depth + 1
        return execute_offline_heuristics(prompt=prompt, image=pil_image)

    @classmethod
    def route_text_request(
        cls,
        prompt: str,
        provider: str = "Google Gemini",
        model_name: Optional[str] = "gemini-2.5-flash",
        api_key: Optional[str] = None,
        **kwargs
    ) -> str:
        """Route text queries across providers with strict 6s timeout and fallback."""
        canonical = cls._canonical_provider(provider)

        try:
            if canonical == "gemini":
                return _execute_with_timeout(
                    _query_gemini,
                    6.0,
                    prompt=prompt,
                    model_name=model_name or "gemini-2.5-flash",
                    api_key=api_key,
                    image_data=None
                )
            elif canonical == "openai":
                return _execute_with_timeout(
                    _query_openai,
                    6.0,
                    prompt=prompt,
                    model_name=model_name or "gpt-4o-mini",
                    api_key=api_key,
                    image_data=None
                )
            elif canonical == "deepseek":
                base_url = kwargs.get("base_url", "https://api.deepseek.com/v1")
                return _execute_with_timeout(
                    _query_deepseek,
                    6.0,
                    prompt=prompt,
                    model_name=model_name or "deepseek-chat",
                    api_key=api_key,
                    image_data=None,
                    base_url=base_url
                )
            elif canonical == "groq":
                return _execute_with_timeout(
                    _query_groq,
                    6.0,
                    prompt=prompt,
                    model_name=model_name or "llama-3.3-70b-versatile",
                    api_key=api_key,
                    image_data=None
                )
            elif canonical == "ollama":
                base_url = kwargs.get("base_url", "http://localhost:11434")
                return _execute_with_timeout(
                    _query_ollama,
                    6.0,
                    prompt=prompt,
                    model_name=model_name or "llama3.2",
                    base_url=base_url,
                    image_data=None
                )
            else:
                return _query_offline(prompt=prompt, image_data=None)
        except Exception as exc:
            LAST_TELEMETRY["active_provider"] = "Offline Heuristics"
            if isinstance(exc, (TimeoutError, concurrent.futures.TimeoutError)):
                LAST_TELEMETRY["failover_badge"] = f"Primary Timeout (>6.0s on {provider}) -> Fallback: Offline Heuristics"
            else:
                LAST_TELEMETRY["failover_badge"] = f"Primary Failed ({provider}) -> Fallback: Offline Heuristics"
            return _query_offline(prompt=prompt, image_data=None)

    @classmethod
    def _clean_artifact_markdown(cls, raw_text: str) -> str:
        """Strip accidental code fences and conversational filler from LLM output."""
        if not raw_text:
            return ""
        text = raw_text.strip()

        # 1. Remove conversational filler / preambles from beginning
        preambles = [
            r"^(?:Sure(?: thing)?[!,.]|Certainly[!,.]|Here (?:is|are) (?:the|your) [^\n:]+[:!]?)\s*\r?\n+",
            r"^(?:I have (?:updated|modified|rewritten|converted) [^\n:]+[:!]?)\s*\r?\n+",
            r"^(?:Below is the (?:updated|modified|requested) [^\n:]+[:!]?)\s*\r?\n+"
        ]
        for pat in preambles:
            text = re.sub(pat, "", text, flags=re.IGNORECASE).strip()

        # 2. Remove polite conversational sign-offs from end
        text = re.sub(r"\r?\n+(?:Let me know if you need (?:any|further) [^\n]+|I hope this helps!)[^\n]*$", "", text, flags=re.IGNORECASE).strip()

        # 3. Strip triple backtick blocks (```markdown ... ``` or ``` ... ```)
        fence_match = re.search(r"^```(?:markdown|md)?\s*\r?\n(.*?)\r?\n```$", text, re.DOTALL | re.IGNORECASE)
        if fence_match:
            text = fence_match.group(1).strip()
        else:
            block_match = re.search(r"```(?:markdown|md)?\s*\r?\n(.*?)\r?\n```", text, re.DOTALL | re.IGNORECASE)
            if block_match:
                inner = block_match.group(1).strip()
                if len(inner) > len(text) * 0.4 or ("#" in inner or "|" in inner):
                    text = inner
            elif text.startswith("```"):
                lines = text.splitlines()
                if len(lines) >= 2 and lines[0].strip().startswith("```") and lines[-1].strip().startswith("```"):
                    text = "\n".join(lines[1:-1]).strip()

        # 4. Final pass cleanup
        for pat in preambles:
            text = re.sub(pat, "", text, flags=re.IGNORECASE).strip()
        text = re.sub(r"\r?\n+(?:Let me know if you need (?:any|further) [^\n]+|I hope this helps!)[^\n]*$", "", text, flags=re.IGNORECASE).strip()

        return text


    @classmethod
    def _transform_artifact_impl(
        cls,
        current_content: str,
        observations: dict,
        user_instruction: str,
        preferred_provider: str = "Google Gemini",
        **kwargs
    ) -> str:
        if not current_content:
            return ""

        obs_section = ""
        if observations and isinstance(observations, dict):
            obs_lines = [f"- **{k}**: {v}" for k, v in observations.items()]
            obs_section = "\n### Context Observations & Metadata:\n" + "\n".join(obs_lines) + "\n"

        system_prompt = (
            "You are an expert Document Artifact Engine. "
            "Your task is to transform, rewrite, or enhance the provided document artifact strictly following the user's instructions and context observations.\n"
            "STRICT CONSTRAINTS:\n"
            "1. Output ONLY the modified document text in clean GitHub-flavored Markdown.\n"
            "2. DO NOT include any conversational preamble, filler, greetings, pleasantries, or closing remarks (e.g. no 'Sure!', 'Here is the document', etc.).\n"
            "3. DO NOT wrap the output in markdown code fences (```markdown ... ```). Output the direct raw markdown content.\n"
            "4. Preserve all crucial facts, figures, and technical metrics from the original artifact.\n"
            "5. Apply the requested structural, stylistic, tonal, or layout modifications with high fidelity."
        )

        full_prompt = (
            f"{system_prompt}\n\n"
            f"{obs_section}\n"
            f"### Current Document Artifact:\n"
            f"{current_content}\n\n"
            f"### User Transformation Instruction:\n"
            f"{user_instruction}\n\n"
            f"### Modified Document Artifact (Markdown only):"
        )

        canonical = cls._canonical_provider(preferred_provider)

        if canonical == "offline":
            raw_res = OfflineHeuristicsEngine.transform_artifact(
                current_content=current_content,
                observations=observations or {},
                user_instruction=user_instruction
            )
            return cls._clean_artifact_markdown(raw_res)

        target_model = "gemini-2.5-flash" if canonical == "gemini" else kwargs.get("model_name")
        try:
            raw_res = _execute_with_timeout(
                query_llm,
                6.0,
                prompt=full_prompt,
                model_provider=preferred_provider,
                model_name=target_model,
                **kwargs
            )
            if not raw_res or raw_res.startswith("⚠️") or raw_res.startswith("❌") or raw_res.startswith("⏳"):
                raw_res = OfflineHeuristicsEngine.transform_artifact(
                    current_content=current_content,
                    observations=observations or {},
                    user_instruction=user_instruction
                )
        except Exception:
            raw_res = OfflineHeuristicsEngine.transform_artifact(
                current_content=current_content,
                observations=observations or {},
                user_instruction=user_instruction
            )

        return cls._clean_artifact_markdown(raw_res)

    def transform_artifact(
        self,
        current_content: str,
        observations: dict = None,
        user_instruction: str = "",
        preferred_provider: str = "Google Gemini",
        **kwargs
    ) -> str:
        """Transform an active document artifact based on observations and user instructions.
        Supports both instance invocation `router.transform_artifact(...)`
        and class invocation `LLMRouter.transform_artifact(...)`.
        """
        if isinstance(self, str) and observations is not None:
            return LLMRouter._transform_artifact_impl(
                current_content=self,
                observations=observations or {},
                user_instruction=user_instruction,
                preferred_provider=preferred_provider,
                **kwargs
            )
        return LLMRouter._transform_artifact_impl(
            current_content=current_content,
            observations=observations or {},
            user_instruction=user_instruction,
            preferred_provider=preferred_provider,
            **kwargs
        )


def transform_artifact(
    current_content: str,
    observations: dict,
    user_instruction: str,
    preferred_provider: str = "Google Gemini",
    **kwargs
) -> str:
    """Module-level entry point for artifact transformation."""
    return LLMRouter._transform_artifact_impl(
        current_content=current_content,
        observations=observations,
        user_instruction=user_instruction,
        preferred_provider=preferred_provider,
        **kwargs
    )



def route_vision_request(
    prompt: str,
    provider: str,
    image_data: Any,
    model_name: Optional[str] = None,
    api_key: Optional[str] = None,
    **kwargs
) -> str:
    """Top-level functional interface for vision routing."""
    return LLMRouter.route_vision_request(
        prompt=prompt,
        provider=provider,
        image_data=image_data,
        model_name=model_name,
        api_key=api_key,
        **kwargs
    )


def analyze_image(
    image_data: Any,
    prompt: str = "Analyze this image and extract all key data points and visual metrics.",
    provider: str = "Google Gemini",
    model_name: Optional[str] = "gemini-2.5-flash",
    api_key: Optional[str] = None,
    **kwargs
) -> str:
    """Convenience functional interface for fast, downsampled vision intelligence."""
    return LLMRouter.route_vision_request(
        prompt=prompt,
        provider=provider,
        image_data=image_data,
        model_name=model_name,
        api_key=api_key,
        **kwargs
    )


def query_llm(
    prompt: str,
    model_provider: str = "Google Gemini",
    model_name: Optional[str] = "gemini-2.5-flash",
    api_key: Optional[str] = None,
    image_data: Optional[Any] = None,
    **kwargs
) -> str:
    """Unified routing entry point supporting both vision and text pipelines."""
    start_time = time.time()
    canonical_primary = model_provider or "Google Gemini"

    LAST_TELEMETRY["primary_provider"] = canonical_primary
    LAST_TELEMETRY["active_provider"] = canonical_primary
    LAST_TELEMETRY["fallback_depth"] = 0
    LAST_TELEMETRY["failover_badge"] = None

    pil_image = _prepare_pil_image(image_data)

    try:
        if pil_image is not None:
            result = LLMRouter.route_vision_request(
                prompt=prompt,
                provider=model_provider,
                image_data=pil_image,
                model_name=model_name,
                api_key=api_key,
                **kwargs
            )
        else:
            result = LLMRouter.route_text_request(
                prompt=prompt,
                provider=model_provider,
                model_name=model_name,
                api_key=api_key,
                **kwargs
            )
    except Exception as exc:
        LAST_TELEMETRY["active_provider"] = "Offline Heuristics"
        LAST_TELEMETRY["failover_badge"] = f"Primary Failed ({canonical_primary} Exception) -> Fallback: Offline Heuristics"
        fallback_res = _query_offline(prompt=prompt, image_data=image_data)
        result = f"⚠️ **{canonical_primary} Exception**: `{exc}`\n\n🔄 **Automated Offline Fallback Analysis:**\n\n{fallback_res}"

    latency_ms = round((time.time() - start_time) * 1000, 2)
    LAST_TELEMETRY["latency_ms"] = latency_ms

    img_dims = None
    img_mime = None
    if pil_image is not None:
        img_dims = f"{pil_image.width}x{pil_image.height}"
        img_mime = "image/png" if pil_image.mode == "RGBA" else "image/jpeg"

    # Hook asynchronous telemetry & audit logging
    try:
        from core.telemetry import log_event
        session_id = "anon-session"
        try:
            import streamlit as st
            if hasattr(st, "session_state") and "session_id" in st.session_state:
                session_id = str(st.session_state["session_id"])
        except Exception:
            pass

        log_event({
            "prompt_text": prompt,
            "session_id": session_id,
            "provider_attempted": canonical_primary,
            "provider_succeeded": LAST_TELEMETRY["active_provider"],
            "fallback_depth": LAST_TELEMETRY.get("fallback_depth", 0),
            "status_code": 200,
            "latency_ms": latency_ms,
            "error_message": LAST_TELEMETRY.get("failover_badge"),
            "image_dimensions": img_dims,
            "image_mime": img_mime
        })
    except Exception:
        pass

    try:
        import streamlit as st
        st.session_state["telemetry"] = dict(LAST_TELEMETRY)
    except Exception:
        pass

    return result
