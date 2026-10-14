# DocuMind AI — RAG Pipeline Specification

## Pipeline Workflow

The DocuMind Advanced RAG pipeline operates through a deterministic 9-stage sequence:

```
[Raw User Query]
       │
       ▼
1. Security Sanitization (Detect prompt injection & secret leakage)
       │
       ▼
2. Conversation-Aware Query Rewriting (Resolve pronouns & context)
       │
       ▼
3. Intent Classification (Fact Lookup, Summary, Comparison, Timeline)
       │
       ▼
4. Hybrid Retrieval (Dense Vector Search + BM25 Keyword Search)
       │
       ▼
5. Reciprocal Rank Fusion (RRF) & Heuristic Re-ranking
       │
       ▼
6. Context Token Budgeting & Deduplication
       │
       ▼
7. Grounded Generation (Extractive Local or Configured LLM)
       │
       ▼
8. Citation Verification (Map output citations to source chunk provenance)
       │
       ▼
[Audited Response + Interactive Verification Chips]
```

## Detailed Pipeline Stages

### 1. Security Sanitization
Before processing, incoming queries are scanned against known prompt injection and jailbreak patterns (e.g., `"ignore previous instructions"`, `"[SYSTEM OVERRIDE]"`). Flagged queries are sanitized and recorded in the audit event log.

### 2. Conversation-Aware Query Rewriting
When users ask follow-up questions (e.g., *"What about its operating margin?"*), the query rewriter references the immediate conversation history to produce a self-contained query: *"What about its operating margin? (in context of: Q3 Financial Summary)"*.

### 3. Intent Classification
Classifies queries into distinct operational intents:
- `comparison`: Activates cross-document comparison and multi-source synthesis.
- `summary`: Allocates broader chunk budget across sections.
- `fact_lookup`: Prioritizes top-ranked passages with exact numerical density.
- `timeline`: Extracts chronological markers and milestone sequences.

### 4. Hybrid Retrieval & Reciprocal Rank Fusion
- **Dense Vector Search**: Measures cosine similarity against indexed chunks.
- **BM25 Keyword Matching**: Uses token frequency to capture specialized acronyms, proper nouns, and serial numbers that vector embeddings might dilute.
- **RRF Equation**:
  $$Score(chunk) = 0.6 \cdot \frac{1}{60 + rank_{dense}} + 0.4 \cdot \frac{1}{60 + rank_{bm25}}$$

### 5. Context Token Budgeting
DocuMind enforces a default context budget of 3,200 tokens. Retrieved chunks are appended in rank order until the budget limit is reached, preventing context truncation or prompt overflow.

### 6. Citation Validation & Source Verification
The generated response is parsed for citation tags matching `[filename, p. X]`. The validator cross-references every cited document and page against the chunks actually retrieved. If a citation maps to a genuine source chunk, it is assigned `is_verified = True` and rendered with a green verification chip.

### 7. Insufficient Evidence Safeguard
If no relevant passages meet the similarity threshold ($0.25$), DocuMind explicitly refuses to speculate:
> *"Insufficient Evidence: No relevant passages were retrieved from the selected document collections to answer your inquiry with high confidence."*
