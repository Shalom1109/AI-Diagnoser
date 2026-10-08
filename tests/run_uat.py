#!/usr/bin/env python3
"""tests/run_uat.py

Standalone Integration and User Acceptance Smoke Test (UAT) script.
Verifies system health, daemon endpoints, secret configurations, and runtime dependencies.

Usage:
    python tests/run_uat.py
"""

import os
import sys
import requests

# Ensure UTF-8 output encoding on Windows consoles
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ANSI Color codes for clean CLI reporting
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def check_streamlit_health(base_url: str = "http://localhost:8501") -> tuple[bool, str]:
    """Ping Streamlit _stcore/health endpoint."""
    endpoint = f"{base_url.rstrip('/')}/_stcore/health"
    try:
        resp = requests.get(endpoint, timeout=3.0)
        if resp.status_code == 200:
            return True, f"HTTP 200 OK ({endpoint})"
        return False, f"HTTP {resp.status_code} ({endpoint})"
    except Exception as e:
        return False, f"Connection refused or server offline ({endpoint})"


def check_ollama_daemon(base_url: str = "http://localhost:11434") -> tuple[bool, str]:
    """Ping Ollama /api/tags endpoint and verify model weights."""
    endpoint = f"{base_url.rstrip('/')}/api/tags"
    try:
        resp = requests.get(endpoint, timeout=3.0)
        if resp.status_code == 200:
            data = resp.json()
            models = [m.get("name", "").lower() for m in data.get("models", [])]
            has_llama = any("llama3.2" in m or "llama3" in m for m in models)
            has_llava = any("llava" in m for m in models)

            status_notes = []
            if has_llama:
                status_notes.append("llama3.2 available")
            if has_llava:
                status_notes.append("llava vision available")

            if not status_notes:
                return True, f"Ollama Active (No recommended models pulled yet: {models})"
            return True, f"Ollama Active ({', '.join(status_notes)})"
        return False, f"HTTP {resp.status_code} from {endpoint}"
    except Exception:
        return False, f"Ollama daemon not reachable at {endpoint}"


def check_secrets_configuration() -> tuple[bool, str]:
    """Validate presence of required master secrets without disclosing keys."""
    keys_to_check = ["gemini_api_key", "openai_api_key", "groq_api_key", "deepseek_api_key"]
    found_keys = []
    missing_keys = []

    # 1. Check .streamlit/secrets.toml
    sec_path = os.path.join(os.getcwd(), ".streamlit", "secrets.toml")
    parsed_toml = {}
    if os.path.isfile(sec_path):
        try:
            import tomllib
            with open(sec_path, "rb") as f:
                parsed_toml = tomllib.load(f)
        except Exception:
            pass

    for k in keys_to_check:
        val = parsed_toml.get(k) or os.getenv(k.upper()) or os.getenv(k)
        if val and str(val).strip():
            found_keys.append(k)
        else:
            missing_keys.append(k)

    if len(found_keys) > 0:
        summary = f"{len(found_keys)} configured ({', '.join(found_keys)}), {len(missing_keys)} missing"
        return True, summary
    else:
        return False, "No cloud LLM API keys found (Running in Zero-Config Offline Mode)"


def check_python_dependencies() -> tuple[bool, str]:
    """Verify presence of core runtime dependencies."""
    required = ["streamlit", "PIL", "requests", "plotly"]
    missing = []
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)

    if not missing:
        return True, f"All core packages loaded ({', '.join(required)})"
    return False, f"Missing packages: {', '.join(missing)}"


def run_smoke_tests():
    print(f"\n{BOLD}{CYAN}======================================================================{RESET}")
    print(f"{BOLD}{CYAN}  Enterprise Multimodal Document Studio - Integration Smoke Test (UAT){RESET}")
    print(f"{BOLD}{CYAN}======================================================================{RESET}\n")

    test_items = [
        ("Core Python Runtime & Packages", check_python_dependencies),
        ("Master Secrets & Environment", check_secrets_configuration),
        ("Streamlit Server Health Endpoint", check_streamlit_health),
        ("Local Ollama Daemon & Models", check_ollama_daemon),
    ]

    results = []
    for name, test_func in test_items:
        passed, detail = test_func()
        results.append((name, passed, detail))

    # Print summary table
    print(f"{'Component Prerequisite':<36} | {'Status':<10} | {'Details'}")
    print("-" * 75)

    all_critical_passed = True
    for name, passed, detail in results:
        status_tag = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
        print(f"{name:<36} | {status_tag:<19} | {detail}")
        # Note: Ollama and Streamlit server are optional for pure offline mode, but we report them cleanly
        if not passed and "Python" in name:
            all_critical_passed = False

    print("-" * 75)
    if all_critical_passed:
        print(f"\n{GREEN}{BOLD}✓ System Smoke Tests Completed Successfully.{RESET}\n")
    else:
        print(f"\n{YELLOW}{BOLD}⚠ System Smoke Tests completed with warnings or missing services.{RESET}\n")


if __name__ == "__main__":
    run_smoke_tests()
