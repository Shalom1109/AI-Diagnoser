"""Configuration constants, color palettes, fonts, and model catalogs."""

THEME_COLORS = {
    "light": {
        "bg_primary": "#F5F1E8",
        "bg_card": "#FFFFFF",
        "text_primary": "#2D2D2D",
        "text_secondary": "#6B655D",
        "border_color": "#E3DCD1",
        "accent_terracotta": "#C65D3B",
        "accent_sage": "#87A878",
        "accent_ochre": "#D4A574",
        "shadow": "rgba(45, 45, 45, 0.06)",
    },
    "dark": {
        "bg_primary": "#1A1A1A",
        "bg_card": "#262626",
        "text_primary": "#F5F1E8",
        "text_secondary": "#A39E93",
        "border_color": "#383838",
        "accent_terracotta": "#D97251",
        "accent_sage": "#98B889",
        "accent_ochre": "#E0B788",
        "shadow": "rgba(0, 0, 0, 0.4)",
    }
}

FONT_PRESETS = {
    "SF Pro (Apple)": '-apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "SF Pro", "Helvetica Neue", sans-serif',
    "Space Grotesk": "'Space Grotesk', sans-serif",
    "Playfair Display": "'Playfair Display', serif",
    "JetBrains Mono": "'JetBrains Mono', monospace",
    "Plus Jakarta Sans": "'Plus Jakarta Sans', sans-serif"
}

# ---------------------------------------------------------------------------
# Primary Model Catalog (One Hardcoded Primary Model Per Provider)
# ---------------------------------------------------------------------------
MODEL_CATALOG = {
    "Google Gemini": {
        "primary_model": "gemini-2.5-flash",
        "models": ["gemini-2.5-flash", "gemini-3.8-flash"],
        "description": "Google's Gemini 2.5 Flash high-speed multimodal intelligence.",
        "requires_api_key": True,
        "supports_vision": True
    },
    "OpenAI": {
        "primary_model": "gpt-4o-mini",
        "models": ["gpt-4o-mini"],
        "description": "OpenAI GPT-4o Mini fast, cost-efficient multimodal reasoning.",
        "requires_api_key": True,
        "supports_vision": True
    },
    "DeepSeek": {
        "primary_model": "deepseek-chat",
        "models": ["deepseek-chat", "deepseek-reasoner"],
        "description": "DeepSeek-V3 and DeepSeek-R1 deep reasoning intelligence via api.deepseek.com/v1.",
        "requires_api_key": True,
        "supports_vision": False,
        "base_url": "https://api.deepseek.com/v1"
    },
    "Groq": {
        "primary_model": "llama-3.3-70b-versatile",
        "models": ["llama-3.3-70b-versatile"],
        "description": "Llama 3.3 70B sub-second inference via Groq LPU engine.",
        "requires_api_key": True,
        "supports_vision": True
    },
    "Ollama": {
        "primary_model": "llama3.2",
        "vision_model": "llava",
        "models": ["llama3.2", "llava", "bakllava"],
        "description": "100% private local execution on your machine via Ollama (using llava for vision).",
        "requires_api_key": False,
        "supports_vision": True,
        "base_url": "http://localhost:11434"
    },
    "Offline Heuristics": {
        "primary_model": "built-in-tf-idf",
        "models": ["built-in-tf-idf"],
        "description": "Pure Python algorithmic analysis with zero external dependencies.",
        "requires_api_key": False,
        "supports_vision": False
    }
}

# Provider to Primary Model Mapping
PROVIDER_PRIMARY_MODELS = {
    "Google Gemini": "gemini-3.8-flash",
    "OpenAI": "gpt-4o-mini",
    "DeepSeek": "deepseek-chat",
    "Groq": "llama-3.3-70b-versatile",
    "Ollama": "llama3.2",
    "Offline Heuristics": "built-in-tf-idf"
}