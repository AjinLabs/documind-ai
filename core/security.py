"""
DocuMind AI — Security, Governance & Safety Engine
Enterprise safeguards:
- Prompt injection defense & threat mitigation
- Secret redaction filter (API keys, credentials, tokens)
- Path traversal defense & safe upload path resolution
- PDF safety verification
- Audit event logging
"""
import re
import os
import logging
from pathlib import Path
from typing import Tuple, Dict, Any
from core.database import log_audit_event

logger = logging.getLogger(__name__)

# Prompt injection signatures
INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|above)\s+instructions", re.IGNORECASE),
    re.compile(r"disregard\s+system\s+prompt", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(DAN|unrestricted|in\s+developer\s+mode)", re.IGNORECASE),
    re.compile(r"reveal\s+(your\s+)?(system\s+prompt|hidden\s+instructions)", re.IGNORECASE),
    re.compile(r"bypass\s+(safety|content\s+filter|guardrails)", re.IGNORECASE),
    re.compile(r"<\|\s*im_start\s*\|>", re.IGNORECASE),
    re.compile(r"\[SYSTEM\s+OVERRIDE\]", re.IGNORECASE)
]

# Sensitive credentials & API key patterns
SECRET_PATTERNS = [
    (re.compile(r"sk-[a-zA-Z0-9]{20,60}"), "[REDACTED_OPENAI_KEY]"),
    (re.compile(r"AIzaSy[a-zA-Z0-9_\-]{33}"), "[REDACTED_GEMINI_KEY]"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "[REDACTED_AWS_KEY]"),
    (re.compile(r"bearer\s+[a-zA-Z0-9_\-\.]{25,}", re.IGNORECASE), "Bearer [REDACTED_TOKEN]"),
    (re.compile(r"password\s*[:=]\s*['\"][^'\"]+['\"]", re.IGNORECASE), "password='[REDACTED_PWD]'")
]

def sanitize_user_input(text: str) -> Tuple[str, bool, str]:
    """
    Scans and sanitizes user input for prompt injection vectors.
    Returns:
        (sanitized_text, is_safe, detected_flag)
    """
    for pattern in INJECTION_PATTERNS:
        match = pattern.search(text)
        if match:
            flag = match.group(0)
            log_audit_event("PROMPT_INJECTION_BLOCKED", {"pattern": flag, "input_sample": text[:100]}, severity="WARNING")
            # Neutralize injection text
            clean_text = pattern.sub("[FILTERED_INJECTION_ATTEMPT]", text)
            return clean_text, False, f"Potential prompt injection pattern detected: '{flag}'"

    return text, True, "Clean"


def redact_secrets(text: str) -> str:
    """Redacts API keys and secrets from output strings or logs."""
    redacted = text
    for pattern, replacement in SECRET_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def sanitize_filename(filename: str) -> str:
    """Prevents path traversal attacks by extracting only the base filename."""
    # Remove directory separators and null bytes
    clean = os.path.basename(filename)
    clean = clean.replace("\x00", "").replace("..", "")
    clean = re.sub(r"[^\w\.\-\_ ]", "_", clean)
    return clean.strip() or "unnamed_document.pdf"


def validate_file_path(target_path: Path, base_dir: Path) -> bool:
    """Guarantees that target_path stays strictly within base_dir."""
    try:
        resolved_target = target_path.resolve()
        resolved_base = base_dir.resolve()
        return resolved_base in resolved_target.parents or resolved_target == resolved_base
    except Exception:
        return False
