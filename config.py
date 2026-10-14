"""
DocuMind AI — Enterprise Intelligence Edition
Configuration and Constants
"""
import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
INDEX_DIR = DATA_DIR / "indexes"
FAISS_DIR = INDEX_DIR / "faiss"
CHROMA_DIR = INDEX_DIR / "chroma"
EXPORTS_DIR = DATA_DIR / "exports"
LOGS_DIR = DATA_DIR / "logs"
SQLITE_DB_PATH = DATA_DIR / "documind.db"

# Create directories if not exist
for directory in [DATA_DIR, UPLOADS_DIR, INDEX_DIR, FAISS_DIR, CHROMA_DIR, EXPORTS_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Product Metadata
APP_NAME = "DocuMind AI"
APP_SUBTITLE = "Enterprise Intelligence Edition"
APP_TAGLINE = "From Documents to Decisions."
VERSION = "3.2.0"

# Design System - "Eliza" Minimalist Editorial Palette
PALETTE = {
    "obsidian": "#151618",      # Deep dark base, primary typography, dark mode background
    "charcoal_silk": "#3C4449", # Primary accent, authoritative buttons, badge borders
    "shadowed_ash": "#62676B",  # Secondary body text, neutral captions
    "cool_concrete": "#8D9295", # Muted labels, secondary indicators, subtle borders
    "morning_mist": "#CED3D6",  # Light dividers, soft badge backgrounds, pill highlights
    "surface_light": "#FFFFFF", # Card background in light mode
    "bg_light": "#F7F8F9",      # Warm architectural paper white
    "surface_dark": "#1E2124",  # Card surface in dark mode
    "bg_dark": "#151618",       # Obsidian background in dark mode
    "border_light": "#E2E6E9",  # Subtle card border in light mode
    "border_dark": "#2A2F35",   # Card border in dark mode
    "success": "#2D6A4F",       # Subtle forest green for verified items
    "warning": "#B07D1E",       # Muted amber for reviews/contradictions
    "danger": "#9E2A2B",        # Brick red for security alerts/insufficient evidence
    "info": "#3C5A78"           # Slate blue for informational chips
}

# Ingestion & Chunking Defaults
DEFAULT_CHUNK_SIZE = 800
DEFAULT_CHUNK_OVERLAP = 150
MAX_UPLOAD_SIZE_MB = 40
ALLOWED_EXTENSIONS = [".pdf", ".txt", ".md"]

# Vector & Embedding Defaults
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384
DEFAULT_VECTOR_STORE = "faiss"  # Options: 'faiss', 'chroma'
DEFAULT_TOP_K = 5
SIMILARITY_THRESHOLD = 0.35

# RAG & Generation Defaults
DEFAULT_LLM_PROVIDER = "extractive"  # Options: 'extractive', 'openai', 'gemini', 'ollama'
SUPPORTED_PROVIDERS = ["extractive", "openai", "gemini", "ollama"]
CONTEXT_TOKEN_BUDGET = 3200

# Agent Research Limits
AGENT_MAX_ITERATIONS = 5
AGENT_MAX_TOOL_CALLS = 10
AGENT_TIMEOUT_SECONDS = 45

# Evaluation Defaults
EVAL_PRECISION_K = 3
EVAL_STARTER_FILE = DATA_DIR / "starter_eval.json"
