# DocuMind AI — RAG Evaluation Harness

## Evaluation Methodology

DocuMind AI includes an integrated evaluation harness (`core/evaluation.py`) designed to measure information retrieval performance, citation integrity, and latency across controlled ground-truth datasets.

## Measured Metrics

### 1. Precision@k
Measures the proportion of retrieved chunks within the top-$k$ results that match expected source documents or ground-truth keywords:
$$\text{Precision}@k = \frac{|\text{Retrieved Chunks} \cap \text{Relevant Chunks}|}{k}$$

### 2. Recall@k
Measures the fraction of expected source documents or page targets retrieved within the top-$k$ results:
$$\text{Recall}@k = \frac{|\text{Retrieved Relevant Targets}|}{|\text{Total Ground Truth Targets}|}$$

### 3. Mean Reciprocal Rank (MRR)
Evaluates where the first relevant chunk appears in the ranked retrieval output:
$$\text{MRR} = \frac{1}{\text{Rank of First Relevant Result}}$$
If the most relevant chunk is retrieved at rank 1, MRR is 1.0; at rank 2, MRR is 0.5.

### 4. Citation Validity Rate
Calculates the percentage of citations generated in the answer that correspond to actual, retrieved source chunks with matching page numbers:
$$\text{Citation Validity} = \frac{\text{Verified In-Text Citations}}{\text{Total Citations Present}}$$

### 5. Groundedness / Faithfulness Score
Estimates the lexical and semantic alignment between the synthesized answer and the retrieved documentary context. Ensures the model is not introducing hallucinated external claims.

### 6. Pipeline Latency
Tracks end-to-end processing turnaround time in milliseconds (including rewriting, retrieval, and synthesis).

## Benchmark Experiment Persistence
All evaluation runs are saved in SQLite (`evaluation_records` table) with:
- `eval_id`
- `experiment_name`
- `dataset_name`
- `retrieval_strategy` (e.g., FAISS + BM25 RRF)
- `embedding_model`
- `metrics_json`
- `created_at`
