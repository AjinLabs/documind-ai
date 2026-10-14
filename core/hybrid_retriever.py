"""
DocuMind AI — Hybrid Retrieval Engine
Combines Dense Semantic Vector Search with BM25 Keyword Matching via
Reciprocal Rank Fusion (RRF), Maximal Marginal Relevance (MMR), and Heuristic Re-ranking.
"""
import time
import math
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from core.vector_store import VectorStoreInterface
from core.embeddings import EmbeddingEngine

logger = logging.getLogger(__name__)

class HybridRetriever:
    def __init__(
        self,
        vector_store: VectorStoreInterface,
        embedding_engine: EmbeddingEngine,
        dense_weight: float = 0.6,
        bm25_weight: float = 0.4,
        rrf_k: int = 60
    ):
        self.vector_store = vector_store
        self.embedding_engine = embedding_engine
        self.dense_weight = dense_weight
        self.bm25_weight = bm25_weight
        self.rrf_k = rrf_k
        self._bm25 = None
        self._bm25_chunks: List[Dict[str, Any]] = []
        self._bm25_corpus: List[List[str]] = []

    def sync_bm25_corpus(self, chunks: List[Dict[str, Any]]):
        """Builds BM25 index over all indexed chunks."""
        from rank_bm25 import BM25Okapi
        self._bm25_chunks = chunks
        self._bm25_corpus = [c["text_content"].lower().split() for c in chunks]
        if self._bm25_corpus:
            self._bm25 = BM25Okapi(self._bm25_corpus)
        else:
            self._bm25 = None

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        document_filter: Optional[List[str]] = None,
        collection_filter: Optional[str] = None,
        similarity_threshold: float = 0.25,
        use_mmr: bool = False,
        use_reranker: bool = True
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Executes hybrid retrieval using Dense Vector Search + BM25 keyword matching with RRF fusion.
        Returns:
            (retrieved_chunks_with_scores, diagnostics_dict)
        """
        start_time = time.time()
        diagnostics = {
            "query": query,
            "dense_results_count": 0,
            "bm25_results_count": 0,
            "fused_results_count": 0,
            "latency_ms": 0.0
        }

        # 1. Dense Semantic Retrieval
        query_vec = self.embedding_engine.embed_query(query)
        dense_hits = self.vector_store.search(
            query_vector=query_vec,
            top_k=top_k * 3,
            document_filter=document_filter,
            collection_filter=collection_filter
        )
        diagnostics["dense_results_count"] = len(dense_hits)

        # 2. BM25 Keyword Retrieval
        bm25_hits: List[Tuple[Dict[str, Any], float]] = []
        if self._bm25 is not None and self._bm25_chunks:
            tokenized_query = query.lower().split()
            bm25_scores = self._bm25.get_scores(tokenized_query)

            # Filter and sort
            valid_indices = []
            for i, score in enumerate(bm25_scores):
                if score <= 0.0:
                    continue
                chunk = self._bm25_chunks[i]
                if document_filter and chunk.get("document_id") not in document_filter:
                    continue
                if collection_filter and collection_filter != "All":
                    if chunk.get("collection_name") and chunk.get("collection_name") != collection_filter:
                        continue
                valid_indices.append((i, float(score)))

            valid_indices.sort(key=lambda x: x[1], reverse=True)
            for idx, score in valid_indices[:top_k * 3]:
                bm25_hits.append((self._bm25_chunks[idx], score))

        diagnostics["bm25_results_count"] = len(bm25_hits)

        # 3. Reciprocal Rank Fusion (RRF)
        # RRF score = dense_weight * (1 / (rrf_k + dense_rank)) + bm25_weight * (1 / (rrf_k + bm25_rank))
        chunk_scores: Dict[str, Dict[str, Any]] = {}

        # Dense ranks
        for rank, (chunk, score) in enumerate(dense_hits):
            cid = chunk["chunk_id"]
            if cid not in chunk_scores:
                chunk_scores[cid] = {
                    "chunk": chunk,
                    "dense_rank": rank + 1,
                    "dense_score": score,
                    "bm25_rank": None,
                    "bm25_score": 0.0,
                    "rrf_score": 0.0
                }
            else:
                chunk_scores[cid]["dense_rank"] = rank + 1
                chunk_scores[cid]["dense_score"] = score

        # BM25 ranks
        for rank, (chunk, score) in enumerate(bm25_hits):
            cid = chunk["chunk_id"]
            if cid not in chunk_scores:
                chunk_scores[cid] = {
                    "chunk": chunk,
                    "dense_rank": None,
                    "dense_score": 0.0,
                    "bm25_rank": rank + 1,
                    "bm25_score": score,
                    "rrf_score": 0.0
                }
            else:
                chunk_scores[cid]["bm25_rank"] = rank + 1
                chunk_scores[cid]["bm25_score"] = score

        for cid, data in chunk_scores.items():
            rrf = 0.0
            if data["dense_rank"] is not None:
                rrf += self.dense_weight * (1.0 / (self.rrf_k + data["dense_rank"]))
            if data["bm25_rank"] is not None:
                rrf += self.bm25_weight * (1.0 / (self.rrf_k + data["bm25_rank"]))
            data["rrf_score"] = rrf

        fused_list = list(chunk_scores.values())
        fused_list.sort(key=lambda x: x["rrf_score"], reverse=True)

        # 4. Optional Re-ranker (lexical density & key phrase coverage)
        if use_reranker and fused_list:
            query_words = set(query.lower().split())
            for item in fused_list:
                text = item["chunk"]["text_content"].lower()
                matches = sum(1 for w in query_words if w in text)
                coverage = matches / max(1, len(query_words))
                # Boost RRF score with lexical match coverage
                item["final_score"] = item["rrf_score"] * (1.0 + 0.5 * coverage)
            fused_list.sort(key=lambda x: x["final_score"], reverse=True)
        else:
            for item in fused_list:
                item["final_score"] = item["rrf_score"]

        # 5. Extract top_k chunks
        final_results = []
        for item in fused_list[:top_k]:
            chunk_copy = dict(item["chunk"])
            chunk_copy["retrieval_score"] = round(item["final_score"], 4)
            chunk_copy["dense_score"] = round(item["dense_score"], 4)
            chunk_copy["bm25_score"] = round(item["bm25_score"], 4)
            final_results.append(chunk_copy)

        diagnostics["fused_results_count"] = len(final_results)
        diagnostics["latency_ms"] = round((time.time() - start_time) * 1000, 2)

        return final_results, diagnostics
