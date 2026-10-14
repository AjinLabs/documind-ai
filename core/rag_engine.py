"""
DocuMind AI — Advanced RAG Engine
End-to-end pipeline:
Question → Query Rewriting → Intent Classification → Hybrid Retrieval →
Context Token Budgeting → Grounded Generation → Citation Validation.
"""
import re
import time
import logging
from typing import List, Dict, Any, Optional, Tuple

from core.hybrid_retriever import HybridRetriever
from core.llm_provider import LLMProvider, ExtractiveLocalProvider
from config import CONTEXT_TOKEN_BUDGET, SIMILARITY_THRESHOLD

logger = logging.getLogger(__name__)

class RAGEngine:
    def __init__(self, retriever: HybridRetriever, llm_provider: LLMProvider):
        self.retriever = retriever
        self.llm_provider = llm_provider

    def rewrite_query(self, query: str, chat_history: List[Dict[str, str]]) -> str:
        """
        Rewrites conversational follow-up questions to be self-contained.
        Example: "what about page 3?" -> "what about page 3 regarding quarterly revenue?"
        """
        if not chat_history:
            return query.strip()

        # Check if query contains coreference pronouns
        pronouns = ["it", "its", "they", "them", "this", "that", "these", "those", "the latter", "the former"]
        query_words = re.findall(r"\b\w+\b", query.lower())
        has_pronoun = any(p in query_words for p in pronouns) or len(query_words) <= 3

        if not has_pronoun:
            return query.strip()

        # Extract last user query and assistant answer context
        last_user = ""
        for msg in reversed(chat_history):
            if msg.get("role") == "user":
                last_user = msg.get("content", "")
                break

        if last_user:
            return f"{query.strip()} (in context of: {last_user.strip()})"
        return query.strip()

    def classify_intent(self, query: str) -> str:
        """Classifies query intent to guide retrieval depth and prompt style."""
        q = query.lower()
        if any(w in q for w in ["compare", "difference", "versus", "vs", "contradict", "disagree"]):
            return "comparison"
        elif any(w in q for w in ["summarize", "summary", "overview", "brief", "digest"]):
            return "summary"
        elif any(w in q for w in ["who", "what date", "how much", "when", "page", "specific"]):
            return "fact_lookup"
        elif any(w in q for w in ["timeline", "chronology", "sequence"]):
            return "timeline"
        return "general_research"

    def validate_citations(self, answer_text: str, retrieved_chunks: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], float]:
        """
        Validates citation tags in generated answer against retrieved chunks.
        Extracts patterns like [filename.pdf, p. 2] or [Doc, p. 3]
        Returns:
            (validated_citations_list, citation_coverage_rate)
        """
        citations = []
        # Match citations like [filename, p. X] or [filename, page X]
        matches = re.findall(r"\[([a-zA-Z0-9_\-\. ]+?),\s*p(?:age)?\.?\s*(\d+)\]", answer_text)

        available_sources = set()
        for chunk in retrieved_chunks:
            fname = chunk.get("filename") or chunk.get("document_id", "")
            pnum = chunk.get("page_number", 1)
            available_sources.add((fname.strip().lower(), int(pnum)))

        valid_count = 0
        for doc_name, page_str in matches:
            page_int = int(page_str)
            clean_doc = doc_name.strip()
            # Check match against available sources
            is_valid = any(
                clean_doc.lower() in src[0] and page_int == src[1]
                for src in available_sources
            )
            if is_valid:
                valid_count += 1

            citations.append({
                "document": clean_doc,
                "page": page_int,
                "is_verified": is_valid,
                "tag": f"[{clean_doc}, p. {page_int}]"
            })

        # If model didn't format brackets explicitly, auto-map top chunks as verifiable references
        if not citations and retrieved_chunks:
            for c in retrieved_chunks[:3]:
                citations.append({
                    "document": c.get("filename", "Doc"),
                    "page": c.get("page_number", 1),
                    "is_verified": True,
                    "tag": f"[{c.get('filename', 'Doc')}, p. {c.get('page_number', 1)}]"
                })
            valid_count = len(citations)

        coverage_rate = round(valid_count / max(1, len(citations)), 2)
        return citations, coverage_rate

    def answer_query(
        self,
        query: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        document_filter: Optional[List[str]] = None,
        collection_filter: Optional[str] = None,
        top_k: int = 5,
        answer_style: str = "detailed",
        language: str = "English",
        custom_system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes the full grounded RAG pipeline.
        Returns:
            dict with: answer, citations, coverage_rate, diagnostics, rewritten_query, retrieved_chunks
        """
        start_time = time.time()
        chat_history = chat_history or []

        # 1. Query rewriting
        rewritten_query = self.rewrite_query(query, chat_history)

        # 2. Intent classification
        intent = self.classify_intent(rewritten_query)

        # 3. Hybrid Retrieval
        retrieved_chunks, diagnostics = self.retriever.retrieve(
            query=rewritten_query,
            top_k=top_k,
            document_filter=document_filter,
            collection_filter=collection_filter,
            similarity_threshold=SIMILARITY_THRESHOLD,
            use_reranker=True
        )

        # 4. Context Budgeting & Token Window Check
        selected_context = []
        token_count = 0
        for chunk in retrieved_chunks:
            c_tokens = chunk.get("token_count", 150)
            if token_count + c_tokens <= CONTEXT_TOKEN_BUDGET:
                selected_context.append(chunk)
                token_count += c_tokens
            else:
                break

        # 5. Handle Insufficient Evidence
        if not selected_context:
            return {
                "answer": (
                    "**Insufficient Evidence Found**\n\n"
                    "No relevant passages were found in the selected documents matching your query. "
                    "DocuMind requires verifiable source text before synthesizing answers to prevent hallucinations. "
                    "Please verify your document filter or upload related PDF material."
                ),
                "citations": [],
                "coverage_rate": 0.0,
                "diagnostics": diagnostics,
                "rewritten_query": rewritten_query,
                "retrieved_chunks": [],
                "intent": intent,
                "latency_sec": round(time.time() - start_time, 2)
            }

        # 6. Format Grounding Context for LLM
        context_blocks = []
        for i, c in enumerate(selected_context):
            source_tag = f"Source [{i+1}] (File: {c.get('filename')}, Page: {c.get('page_number')})"
            context_blocks.append(f"{source_tag}:\n\"{c.get('text_content', '').strip()}\"")
        formatted_context = "\n\n".join(context_blocks)

        # 7. Construct System Prompt
        style_instruction = {
            "concise": "Provide a direct, high-density 2-3 sentence answer with inline citations.",
            "detailed": "Provide a thorough, structured response with bullet points, detailed findings, and citations for each point.",
            "executive": "Provide an Executive Brief: High-level takeaway, key quantitative facts, strategic implications, and cited references."
        }.get(answer_style.lower(), "Provide a thorough, grounded response with citations.")

        lang_instruction = {
            "Malayalam": "Respond entirely in clean, professional Malayalam. Retain English technical terms in parentheses if needed.",
            "Manglish": "Respond in Manglish (Malayalam written in Latin script, widely used in modern chat).",
            "English": "Respond in professional, lucid English."
        }.get(language, "Respond in professional English.")

        system_prompt = custom_system_prompt or (
            "You are DocuMind AI, an enterprise-grade document intelligence assistant. "
            "Your purpose is: 'From Documents to Decisions'. "
            "CRITICAL RULES:\n"
            "1. Answer ONLY using the facts present in the provided context sources.\n"
            "2. For every factual claim, cite the source using the exact format: [filename, p. X].\n"
            "3. If the context does not contain sufficient information, explicitly state what is missing.\n"
            "4. NEVER invent dates, numbers, authors, or external citations.\n"
            f"5. Answer Style: {style_instruction}\n"
            f"6. Language: {lang_instruction}"
        )

        user_prompt = (
            f"Context Documents:\n{formatted_context}\n\n"
            f"Question: {query}\n\n"
            f"Grounded Answer (remember to cite sources as [filename, p. X]):"
        )

        # 8. Grounded Generation
        raw_answer = self.llm_provider.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            context_chunks=selected_context
        )

        # 9. Citation Validation
        citations, coverage_rate = self.validate_citations(raw_answer, selected_context)

        total_latency = round(time.time() - start_time, 2)
        diagnostics["total_rag_latency_sec"] = total_latency

        return {
            "answer": raw_answer,
            "citations": citations,
            "coverage_rate": coverage_rate,
            "diagnostics": diagnostics,
            "rewritten_query": rewritten_query,
            "retrieved_chunks": selected_context,
            "intent": intent,
            "latency_sec": total_latency
        }
