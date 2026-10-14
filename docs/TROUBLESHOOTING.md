# DocuMind AI — Troubleshooting Guide

## Common Issues & Resolutions

### 1. "No module named 'core'" when running Pytest
- **Cause**: Python path did not register the workspace root.
- **Resolution**: Run tests using `python -m pytest tests/ -v`. The included `conftest.py` automatically injects the repository root into `sys.path`.

### 2. HuggingFace Symlink Warning on Windows
- **Symptom**: `UserWarning: huggingface_hub cache-system uses symlinks by default...`
- **Resolution**: This is a harmless Windows operating system warning. Model caching falls back to standard file duplication. To suppress it in PowerShell:
  ```powershell
  $env:HF_HUB_DISABLE_SYMLINKS_WARNING="1"
  ```

### 3. Scanned PDF Extraction Yields Empty Text
- **Symptom**: Document is uploaded, but shows 0 characters or page extraction shows empty content.
- **Cause**: The PDF consists of scanned raster images rather than text glyphs.
- **Resolution**: DocuMind's PDF engine automatically detects this and marks `is_scanned = 1` with a "Scanned/OCR" badge in the Knowledge Library.

### 4. Vector Dimension Mismatch Notice
- **Symptom**: `FAISS index incompatible: saved with ... current is ... Rebuilding empty index.`
- **Cause**: The embedding model was changed to one with different vector dimensions (e.g., 384 vs 768).
- **Resolution**: DocuMind protects against cross-model corruption by resetting the vector index safely and logging an audit event. Re-ingest documents under the new model.

### 5. Streamlit Port Conflict (`8501 already in use`)
- **Resolution**: Specify a custom port:
  ```powershell
  streamlit run app.py --server.port 8502
  ```

### 6. SQLite Database Locked (`sqlite3.OperationalError: database is locked`)
- **Resolution**: DocuMind configures SQLite with Write-Ahead Logging (`WAL` mode) and a 20-second timeout, allowing concurrent readers and writers without lock contention.
