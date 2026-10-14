"""
DocuMind AI — Multi-Provider LLM & Extractive Answering Engine
Provides unified LLM generation across OpenAI, Google Gemini, Ollama,
and a high-precision, API-free Extractive Local Provider that runs 100% offline.
"""
import os
import re
import json
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, system_prompt: str = "", context_chunks: Optional[List[Dict[str, Any]]] = None) -> str:
        pass


# ==========================================
# 1. API-Free Extractive Local Provider
# ==========================================

class ExtractiveLocalProvider(LLMProvider):
    """
    100% offline, API-free grounded synthesis engine.
    Extracts high-salience sentences matching query keywords and semantic units,
    synthesizes a structured response, and strictly avoids hallucinations.
    """
    def __init__(self):
        self.name = "Extractive Local (API-Free)"

    def generate(self, prompt: str, system_prompt: str = "", context_chunks: Optional[List[Dict[str, Any]]] = None) -> str:
        if not context_chunks:
            return (
                "**Insufficient Evidence**: No relevant passages were retrieved from the selected "
                "document collections to answer your inquiry with high confidence."
            )

        # Extract key question terms
        query_match = re.search(r"Question:\s*(.+?)(?:\n|$)", prompt, re.IGNORECASE)
        question = query_match.group(1).strip() if query_match else prompt
        query_terms = set(re.findall(r"\w{3,}", question.lower()))

        extracted_findings = []
        cited_sources = []

        for i, chunk in enumerate(context_chunks):
            doc_id = chunk.get("filename") or chunk.get("document_id", "Document")
            page = chunk.get("page_number", 1)
            text = chunk.get("text_content", "")

            # Break into sentences
            sentences = re.split(r"(?<=[.!?])\s+", text)
            relevant_sentences = []

            for sent in sentences:
                sent_clean = sent.strip()
                if not sent_clean or len(sent_clean) < 20:
                    continue
                sent_terms = set(re.findall(r"\w{3,}", sent_clean.lower()))
                overlap = query_terms.intersection(sent_terms)
                if overlap or i == 0:  # Top chunk gets priority
                    score = len(overlap)
                    relevant_sentences.append((score, sent_clean))

            if relevant_sentences:
                relevant_sentences.sort(key=lambda x: x[0], reverse=True)
                top_sent = relevant_sentences[0][1]
                extracted_findings.append({
                    "sentence": top_sent,
                    "doc": doc_id,
                    "page": page,
                    "source_ref": f"[{doc_id}, p. {page}]"
                })
                cited_sources.append(f"• **{doc_id}** — Page {page}")

        if not extracted_findings:
            return (
                "**Grounded Extractive Summary**\n\n"
                f"Based on the retrieved context from `{context_chunks[0].get('filename')}` (p. {context_chunks[0].get('page_number')}):\n\n"
                f"> \"{context_chunks[0].get('text_content', '')[:300]}...\"\n\n"
                f"*Note: Running in API-free extractive mode.*"
            )

        # Synthesize coherent response
        lines = ["### Grounded Research Findings", ""]
        seen_sents = set()
        for idx, item in enumerate(extracted_findings[:4]):
            s = item["sentence"]
            if s in seen_sents:
                continue
            seen_sents.add(s)
            lines.append(f"- {s} **{item['source_ref']}**")

        lines.append("")
        lines.append("---")
        lines.append("#### Sources Consulted:")
        for s in list(dict.fromkeys(cited_sources))[:4]:
            lines.append(s)

        lines.append("\n*Generated using DocuMind Extractive Local Engine (100% grounded in source text, zero hallucinations).*")
        return "\n".join(lines)


# ==========================================
# 2. OpenAI Provider
# ==========================================

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model

    def generate(self, prompt: str, system_prompt: str = "", context_chunks: Optional[List[Dict[str, Any]]] = None) -> str:
        if not self.api_key:
            return ExtractiveLocalProvider().generate(prompt, system_prompt, context_chunks)
        try:
            import httpx
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.2
            }
            with httpx.Client(timeout=35.0) as client:
                res = client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    logger.warning(f"OpenAI error {res.status_code}: {res.text}. Falling back to Extractive Local.")
                    return ExtractiveLocalProvider().generate(prompt, system_prompt, context_chunks)
        except Exception as e:
            logger.error(f"OpenAI request exception: {e}. Falling back.")
            return ExtractiveLocalProvider().generate(prompt, system_prompt, context_chunks)


# ==========================================
# 3. Google Gemini Provider
# ==========================================

class GeminiProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.model = model

    def generate(self, prompt: str, system_prompt: str = "", context_chunks: Optional[List[Dict[str, Any]]] = None) -> str:
        if not self.api_key:
            return ExtractiveLocalProvider().generate(prompt, system_prompt, context_chunks)
        try:
            import httpx
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            payload = {
                "contents": [{"parts": [{"text": full_prompt}]}],
                "generationConfig": {"temperature": 0.2}
            }
            with httpx.Client(timeout=35.0) as client:
                res = client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        if parts:
                            return parts[0].get("text", "")
                logger.warning(f"Gemini error: {res.text}. Falling back.")
                return ExtractiveLocalProvider().generate(prompt, system_prompt, context_chunks)
        except Exception as e:
            logger.error(f"Gemini request exception: {e}. Falling back.")
            return ExtractiveLocalProvider().generate(prompt, system_prompt, context_chunks)


# ==========================================
# 4. Ollama Provider
# ==========================================

class OllamaProvider(LLMProvider):
    def __init__(self, host: str = "http://localhost:11434", model: str = "llama3.2"):
        self.host = host
        self.model = model

    def generate(self, prompt: str, system_prompt: str = "", context_chunks: Optional[List[Dict[str, Any]]] = None) -> str:
        try:
            import httpx
            url = f"{self.host}/api/generate"
            payload = {
                "model": self.model,
                "prompt": prompt,
                "system": system_prompt,
                "stream": False
            }
            with httpx.Client(timeout=40.0) as client:
                res = client.post(url, json=payload)
                if res.status_code == 200:
                    return res.json().get("response", "")
                logger.warning(f"Ollama error {res.status_code}. Falling back.")
                return ExtractiveLocalProvider().generate(prompt, system_prompt, context_chunks)
        except Exception as e:
            logger.warning(f"Ollama connection error: {e}. Falling back to Extractive Local.")
            return ExtractiveLocalProvider().generate(prompt, system_prompt, context_chunks)


def get_llm_provider(provider_type: str = "extractive", api_key: Optional[str] = None) -> LLMProvider:
    """Factory method for LLM providers."""
    ptype = provider_type.lower()
    if ptype == "openai":
        return OpenAIProvider(api_key=api_key)
    elif ptype == "gemini":
        return GeminiProvider(api_key=api_key)
    elif ptype == "ollama":
        return OllamaProvider()
    return ExtractiveLocalProvider()
