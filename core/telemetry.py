"""core/telemetry.py

Lightweight, non-blocking telemetry and privacy-preserving audit logger.
Features:
1. Append-only JSON Lines format (logs/telemetry.jsonl).
2. Size-based automatic log rotation (10MB max per file, 5 backup files).
3. Non-blocking asynchronous background thread writing to prevent UI thread lag.
4. Privacy redaction: Prompts and binary buffers are hashed and summarized.
5. Audit interface functions: `log_event(...)` and `get_recent_events(...)`.
"""

import datetime
import hashlib
import json
import os
import shutil
import threading
from typing import Any, Dict, List, Optional

LOG_DIR = os.path.join(os.getcwd(), "logs")
LOG_FILE = os.path.join(LOG_DIR, "telemetry.jsonl")
MAX_BYTES = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5

_write_lock = threading.Lock()


def _rotate_logs_if_needed():
    """Rotate log files if current log file exceeds 10MB."""
    if not os.path.exists(LOG_FILE):
        return

    try:
        if os.path.getsize(LOG_FILE) >= MAX_BYTES:
            # Rotate backups 4 -> 5, 3 -> 4, etc.
            for i in range(BACKUP_COUNT - 1, 0, -1):
                sfile = f"{LOG_FILE}.{i}"
                dfile = f"{LOG_FILE}.{i + 1}"
                if os.path.exists(sfile):
                    if i + 1 > BACKUP_COUNT:
                        os.remove(sfile)
                    else:
                        shutil.move(sfile, dfile)

            # Move active log file to telemetry.jsonl.1
            shutil.move(LOG_FILE, f"{LOG_FILE}.1")
    except Exception:
        pass


def _write_event_async(event_record: Dict[str, Any]):
    """Background worker function for asynchronous file writing."""
    with _write_lock:
        try:
            os.makedirs(LOG_DIR, exist_ok=True)
            _rotate_logs_if_needed()

            line = json.dumps(event_record, ensure_ascii=False) + "\n"
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception:
            pass


def log_event(event_dict: Dict[str, Any]):
    """Asynchronously logs an enterprise audit event.

    Expected fields in event_dict:
    - prompt_text: raw text (hashed & measured for length, never stored raw)
    - session_id: unique session ID or anon identifier
    - provider_attempted: requested primary model provider
    - provider_succeeded: actual provider that returned output
    - fallback_depth: 0 if primary succeeded, 1+ if failovers occurred
    - status_code: 200 for OK, 429/402/500/etc for error
    - latency_ms: response duration in milliseconds
    - error_message: optional error string
    - image_dimensions: optional "WxH" string
    - image_mime: optional mime type string
    """
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    prompt_raw = str(event_dict.get("prompt_text", ""))
    payload_hash = hashlib.sha256(prompt_raw.encode("utf-8")).hexdigest()[:16] if prompt_raw else "empty"

    record = {
        "timestamp": now_iso,
        "session_id": str(event_dict.get("session_id", "anon-session")),
        "payload_hash": payload_hash,
        "payload_char_length": len(prompt_raw),
        "image_dimensions": event_dict.get("image_dimensions"),
        "image_mime": event_dict.get("image_mime"),
        "provider_attempted": str(event_dict.get("provider_attempted", "Unknown")),
        "provider_succeeded": str(event_dict.get("provider_succeeded", "Unknown")),
        "fallback_depth": int(event_dict.get("fallback_depth", 0)),
        "status_code": int(event_dict.get("status_code", 200)),
        "latency_ms": round(float(event_dict.get("latency_ms", 0.0)), 2),
        "error_message": event_dict.get("error_message")
    }

    # Dispatch to background thread to ensure non-blocking UI performance
    t = threading.Thread(target=_write_event_async, args=(record,), daemon=True)
    t.start()


def get_recent_events(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve the most recent audit telemetry events for Streamlit UI dashboards."""
    if not os.path.exists(LOG_FILE):
        return []

    events = []
    with _write_lock:
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in reversed(lines):
                    line_str = line.strip()
                    if line_str:
                        try:
                            events.append(json.loads(line_str))
                            if len(events) >= limit:
                                break
                        except Exception:
                            continue
        except Exception:
            return []

    return events
