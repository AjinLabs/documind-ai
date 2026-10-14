"""
DocuMind AI — Embedding Engine
Provides batch embedding generation using SentenceTransformers with an offline
deterministic fallback that requires no external network or pre-downloaded weights.
"""
import hashlib
import logging
import numpy as np
from typing import List, Union
from config import DEFAULT_EMBEDDING_MODEL, EMBEDDING_DIM

logger = logging.getLogger(__name__)

class EmbeddingEngine:
    def __init__(self, model_name: str = DEFAULT_EMBEDDING_MODEL):
        self.model_name = model_name
        self.dim = EMBEDDING_DIM
        self._st_model = None
        self._fallback_mode = False
        self._initialize_model()

    def _initialize_model(self):
        """Attempts to load sentence-transformers model; gracefully falls back if unavailable."""
        try:
            from sentence_transformers import SentenceTransformer
            # Load with local cache or download
            self._st_model = SentenceTransformer(self.model_name)
            self.dim = self._st_model.get_sentence_embedding_dimension()
            logger.info(f"Loaded SentenceTransformer: {self.model_name} (dim={self.dim})")
        except Exception as e:
            logger.warning(f"Could not load SentenceTransformer '{self.model_name}': {e}. Using deterministic local embedding fallback.")
            self._fallback_mode = True
            self.dim = EMBEDDING_DIM

    def is_fallback(self) -> bool:
        """Returns True if running in deterministic local fallback mode."""
        return self._fallback_mode

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        Embeds a list of text strings into normalized float32 vectors.
        Output shape: (len(texts), dim)
        """
        if not texts:
            return np.empty((0, self.dim), dtype=np.float32)

        if self._st_model is not None and not self._fallback_mode:
            try:
                embeddings = self._st_model.encode(
                    texts,
                    batch_size=32,
                    show_progress_bar=False,
                    normalize_embeddings=True,
                    convert_to_numpy=True
                )
                return embeddings.astype(np.float32)
            except Exception as e:
                logger.error(f"Error in SentenceTransformer encoding: {e}. Falling back.")

        # Deterministic offline n-gram semantic projection
        return self._deterministic_fallback_embed(texts)

    def embed_query(self, query: str) -> np.ndarray:
        """Embeds a single search query."""
        vec = self.embed_texts([query])
        return vec[0]

    def _deterministic_fallback_embed(self, texts: List[str]) -> np.ndarray:
        """
        Deterministic, offline bag-of-words / character n-gram pseudo-embedding.
        Maps text to an L2-normalized 384-dimensional vector space.
        Guarantees that similar texts share vector projections without downloading models.
        """
        vectors = np.zeros((len(texts), self.dim), dtype=np.float32)

        for i, text in enumerate(texts):
            clean = text.lower().strip()
            tokens = clean.split()
            if not tokens:
                vectors[i, 0] = 1.0
                continue

            vec = np.zeros(self.dim, dtype=np.float32)
            # Word level hashing
            for word in tokens:
                h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
                idx = h % self.dim
                sign = 1.0 if (h >> 8) & 1 else -1.0
                vec[idx] += sign

            # Character 3-gram hashing for subword captures
            for j in range(len(clean) - 2):
                tri = clean[j:j+3]
                h_tri = int(hashlib.md5(tri.encode("utf-8")).hexdigest(), 16)
                idx = h_tri % self.dim
                sign = 0.5 if (h_tri >> 8) & 1 else -0.5
                vec[idx] += sign

            # L2 Normalize
            norm = np.linalg.norm(vec)
            if norm > 0:
                vectors[i] = vec / norm
            else:
                vectors[i, 0] = 1.0

        return vectors


# Global singleton instance for efficient caching
_embedding_instance = None

def get_embedding_engine(model_name: str = DEFAULT_EMBEDDING_MODEL) -> EmbeddingEngine:
    global _embedding_instance
    if _embedding_instance is None or _embedding_instance.model_name != model_name:
        _embedding_instance = EmbeddingEngine(model_name)
    return _embedding_instance
