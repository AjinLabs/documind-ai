# DocuMind AI — Enterprise Intelligence Edition

<div align="center">

### *"From Documents to Decisions."*

[![Python](https://img.shields.io/badge/Python-3.10%20--%203.14-151618?style=flat-square&logo=python&logoColor=CED3D6)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.55+-3C4449?style=flat-square&logo=streamlit&logoColor=FFFFFF)](https://streamlit.io)
[![Vector Engines](https://img.shields.io/badge/Vectors-FAISS%20%7C%20ChromaDB-62676B?style=flat-square)](https://github.com/facebookresearch/faiss)
[![Tests](https://img.shields.io/badge/Tests-18%20Passed%20(100%25)-2D6A4F?style=flat-square&logo=pytest&logoColor=FFFFFF)](tests/)
[![Palette](https://img.shields.io/badge/Theme-Eliza%20Minimalist-8D9295?style=flat-square)](design_system.py)
[![License](https://img.shields.io/badge/License-Apache%202.0-CED3D6?style=flat-square)](LICENSE)

</div>

---

## Executive Overview

**DocuMind AI** is an enterprise-grade document intelligence platform designed to transform unstructured PDF corpora into searchable, verifiable, and connected knowledge. 

Unlike generic PDF chat wrappers that hallucinate facts and invent sources, DocuMind maintains **strict page-level provenance** across every stage of processing. Every generated claim is linked directly to an exact document and 1-indexed physical page number.

---

## Aesthetic Design: The "Eliza" Minimalist Editorial Palette

DocuMind is crafted with a calm, architectural, human-centered aesthetic inspired by editorial publications:

<div align="center">

| Token Name | Hex Code | Visual Application |
| :--- | :--- | :--- |
| **Obsidian** | `#151618` | Deep dark tone, primary typography, dark mode background |
| **Charcoal Silk** | `#3C4449` | Primary accent, authoritative buttons, badge borders |
| **Shadowed Ash** | `#62676B` | Secondary body text, neutral captions |
| **Cool Concrete** | `#8D9295` | Muted labels, secondary indicators, subtle borders |
| **Morning Mist** | `#CED3D6` | Light dividers, soft badge backgrounds, pill highlights |
| **Architectural White** | `#FFFFFF` / `#F7F8F9` | Clean card surfaces, warm paper background |

</div>

---

## Core Capabilities & Architectural Innovations

### 1. 🤖 Bounded Agentic Research Orchestrator
- Autonomous state machine that decomposes complex inquiries into multi-step research plans.
- Sandboxed tools: document discovery, evidence extraction, cross-document comparison, and claim validation.
- Guaranteed termination via strict iteration caps (`max_iterations = 5`, `max_tool_calls = 10`) and execution timeouts.
- Generates publication-ready intelligence briefs with executive summaries, findings by source, and explicit limitations.

### 2. ⚖️ Evidence & Contradiction Intelligence Engine
- Scans atomic assertions, figures, dates, and obligations across documents.
- Automatically flags cross-document discrepancies (e.g., conflicting revenue numbers, opposing verbs).
- Displays conflicting passages side-by-side with exact page numbers.
- Integrated Reviewer Ledger for human adjudication (`supported`, `potentially_contradicted`, `requires_human_review`).

### 3. 🕸️ Provenance-Backed Knowledge Graph
- Extracts entities (Organizations, People, Dates, Policies, Topics) and directed relationships from indexed chunks.
- Entity resolution workflow normalizes legal variants (e.g., *"Google LLC"* $\rightarrow$ *"Google"*).
- Interactive visualization using Pyvis and vis.js canvas with hover tooltips displaying source evidence passages.

### 4. 🔬 Document Version Diff Intelligence
- Deterministic diff analysis comparing two document revisions.
- Detects added and removed clauses, shifted dates, and altered numerical values.
- Computes sequence-matcher similarity percentages and highlights altered obligations.

### 5. ⚡ Hybrid Retrieval (Dense Vector + BM25 RRF)
- Dense semantic vector search (FAISS or ChromaDB) paired with exact keyword matching via BM25.
- Rank aggregation using Reciprocal Rank Fusion (RRF) with configurable weights ($k=60$).
- Lexical re-ranking to boost exact phrase alignment.

### 6. 🛡️ Enterprise Security & Governance
- Built-in prompt injection defense that neutralizes jailbreak attempts.
- Secret redaction filter masks OpenAI keys, Gemini keys, AWS credentials, and passwords.
- Path traversal defense ensures uploads remain strictly inside sandboxed directories.
- Append-only immutable audit trail in SQLite.

---

## 13 Integrated Functional Navigation Sections

1. **🧭 Command Center**: Knowledge metrics, indexed collections, recent tasks, and live system health.
2. **💬 AI Research Workspace**: Multi-turn chat with citation chips, source preview drawer, multilingual output (English, Malayalam, Manglish), and style modes.
3. **📚 Knowledge Library**: Document collection manager, chunk inspector, and safe cascading deletion.
4. **🕸️ Knowledge Graph Explorer**: Interactive entity and relationship visualization.
5. **⚖️ Evidence & Contradiction Lab**: Cross-document claim analysis and reviewer adjudication ledger.
6. **🔬 Document Intelligence Studio**: 14 tools (Executive Brief, Summaries, Glossary, Timeline, Action Items, Pydantic JSON, Version Diff, Table Extraction) with PDF and Markdown export.
7. **🤖 Agent Control Room**: Bounded research launcher, execution plans, tool call logs, and report synthesis.
8. **📊 RAG Evaluation Lab**: Precision@k, Recall@k, MRR, Groundedness, and latency benchmarking.
9. **🖋️ Prompt Engineering Studio**: Persona templates (Research Analyst, Executive, Verifier), custom instructions, and live testing.
10. **📜 Conversation History**: Persistent session manager with search, resume, and markdown export.
11. **📥 Data Sources & Ingestion**: PDF upload center, SHA-256 duplicate detection, PyMuPDF extraction, and batch embedding.
12. **🛡️ Security & Governance**: Prompt injection defenses, secret redactor tester, and immutable audit logs.
13. **⚙️ Settings & System Observability**: Vector engine toggle (FAISS / ChromaDB), LLM credentials, and storage diagnostics.

---

## Quickstart Guide (Windows PowerShell)

### 1. Clone Repository
```powershell
git clone https://github.com/AjinLabs/documind-ai.git
cd documind-ai
```

### 2. Set Up Virtual Environment & Dependencies
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Run Automated Tests
```powershell
python -m pytest tests/ -v
```
*(All 18 unit and integration tests run offline without external API keys!)*

### 4. Launch Application
```powershell
streamlit run app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## Deployment Options

- **Streamlit Community Cloud (Free 1-Click)**: Connect [share.streamlit.io](https://share.streamlit.io) to `https://github.com/AjinLabs/documind-ai` and select `app.py`.
- **Render.com**: Connect the repository using the included `render.yaml` blueprint.
- **Docker**: Build container image using `docker build -t documind-ai .` and run `docker run -p 8501:8501 documind-ai`.
- **Vercel**: Includes `vercel.json` and `api/index.py` serverless gateway.

---

## Documentation Index

- [Architecture Specification](docs/ARCHITECTURE.md)
- [RAG Pipeline Deep Dive](docs/RAG_PIPELINE.md)
- [Agentic Research Orchestrator](docs/AGENTIC_RESEARCH.md)
- [Security & Governance](docs/SECURITY.md)
- [Evaluation Harness & Metrics](docs/EVALUATION.md)
- [Setup & Installation](docs/SETUP.md)
- [Troubleshooting Guide](docs/TROUBLESHOOTING.md)
- [Technical Interview Master Guide (65 Q&As)](docs/INTERVIEW_PREPARATION.md)
