"""
DocuMind AI — Unified Vector Store Interface
Provides independent, interchangeable FAISS and ChromaDB backends
with metadata filtering, document deletion, and index compatibility safeguards.
"""
import os
import json
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from config import FAISS_DIR, CHROMA_DIR, DEFAULT_EMBEDDING_MODEL, EMBEDDING_DIM

logger = logging.getLogger(__name__)

class VectorStoreInterface(ABC):
    @abstractmethod
    def add_chunks(self, chunks: List[Dict[str, Any]], embeddings: np.ndarray):
        """Adds chunks and their embedding vectors to the index."""
        pass

    @abstractmethod
    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 5,
        document_filter: Optional[List[str]] = None,
        collection_filter: Optional[str] = None
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Returns list of (chunk_dict, score) tuples."""
        pass

    @abstractmethod
    def delete_document(self, document_id: str):
        """Removes all vectors associated with document_id."""
        pass

    @abstractmethod
    def count(self) -> int:
        """Returns total vectors indexed."""
        pass

    @abstractmethod
    def clear(self):
        """Resets the vector index."""
        pass


# ==========================================
# 1. FAISS Backend Implementation
# ==========================================

class FAISSVectorStore(VectorStoreInterface):
    def __init__(self, index_dir=FAISS_DIR, model_name: str = DEFAULT_EMBEDDING_MODEL, dim: int = EMBEDDING_DIM):
        self.index_dir = index_dir
        self.index_file = self.index_dir / "index.faiss"
        self.meta_file = self.index_dir / "metadata.json"
        self.model_name = model_name
        self.dim = dim
        self.index = None
        self.chunk_metadata: List[Dict[str, Any]] = []
        self._load_or_create()

    def _load_or_create(self):
        import faiss
        if self.index_file.exists() and self.meta_file.exists():
            try:
                with open(self.meta_file, "r", encoding="utf-8") as f:
                    meta_package = json.load(f)

                # Validate embedding model compatibility
                saved_model = meta_package.get("model_name")
                saved_dim = meta_package.get("dim")
                if saved_model != self.model_name or saved_dim != self.dim:
                    logger.warning(
                        f"FAISS index incompatible: saved with {saved_model} (dim={saved_dim}), "
                        f"current is {self.model_name} (dim={self.dim}). Rebuilding empty index."
                    )
                    self._create_empty_index()
                    return

                self.index = faiss.read_index(str(self.index_file))
                self.chunk_metadata = meta_package.get("chunks", [])
                logger.info(f"Loaded FAISS index with {len(self.chunk_metadata)} vectors.")
                return
            except Exception as e:
                logger.error(f"Failed to load FAISS index: {e}. Reinitializing.")

        self._create_empty_index()

    def _create_empty_index(self):
        import faiss
        # Inner Product on normalized vectors is cosine similarity
        self.index = faiss.IndexFlatIP(self.dim)
        self.chunk_metadata = []
        self._save()

    def _save(self):
        import faiss
        if self.index is not None:
            faiss.write_index(self.index, str(self.index_file))
            with open(self.meta_file, "w", encoding="utf-8") as f:
                json.dump({
                    "model_name": self.model_name,
                    "dim": self.dim,
                    "chunks": self.chunk_metadata
                }, f)

    def add_chunks(self, chunks: List[Dict[str, Any]], embeddings: np.ndarray):
        if len(chunks) == 0:
            return
        embeddings = np.ascontiguousarray(embeddings, dtype=np.float32)
        self.index.add(embeddings)
        self.chunk_metadata.extend(chunks)
        self._save()

    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 5,
        document_filter: Optional[List[str]] = None,
        collection_filter: Optional[str] = None
    ) -> List[Tuple[Dict[str, Any], float]]:
        if self.index is None or self.index.ntotal == 0 or len(self.chunk_metadata) == 0:
            return []

        query = np.ascontiguousarray(query_vector.reshape(1, -1), dtype=np.float32)
        search_k = min(len(self.chunk_metadata), max(top_k * 4, 20))
        distances, indices = self.index.search(query, search_k)

        results: List[Tuple[Dict[str, Any], float]] = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(self.chunk_metadata):
                continue
            chunk = self.chunk_metadata[idx]

            # Document ID filter
            if document_filter and chunk.get("document_id") not in document_filter:
                continue

            # Collection filter
            if collection_filter and collection_filter != "All":
                if chunk.get("collection_name") and chunk.get("collection_name") != collection_filter:
                    continue

            results.append((chunk, float(dist)))
            if len(results) >= top_k:
                break

        return results

    def delete_document(self, document_id: str):
        """Rebuilds the index excluding the deleted document's vectors."""
        if not self.chunk_metadata:
            return

        remaining_indices = [i for i, c in enumerate(self.chunk_metadata) if c.get("document_id") != document_id]
        if len(remaining_indices) == len(self.chunk_metadata):
            return  # No vectors to delete

        import faiss
        new_index = faiss.IndexFlatIP(self.dim)
        new_chunks = []

        if remaining_indices:
            # Reconstruct remaining vectors
            vectors = np.zeros((len(remaining_indices), self.dim), dtype=np.float32)
            for new_i, old_i in enumerate(remaining_indices):
                vec = self.index.reconstruct(int(old_i))
                vectors[new_i] = vec
                new_chunks.append(self.chunk_metadata[old_i])
            new_index.add(vectors)

        self.index = new_index
        self.chunk_metadata = new_chunks
        self._save()
        logger.info(f"Deleted document {document_id} from FAISS. Remaining: {len(new_chunks)}")

    def count(self) -> int:
        return self.index.ntotal if self.index else 0

    def clear(self):
        self._create_empty_index()


# ==========================================
# 2. ChromaDB Backend Implementation
# ==========================================

class ChromaVectorStore(VectorStoreInterface):
    def __init__(self, persist_dir=CHROMA_DIR, collection_name: str = "documind_collection", model_name: str = DEFAULT_EMBEDDING_MODEL):
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        self.model_name = model_name
        self._client = None
        self._collection = None
        self._init_chroma()

    def _init_chroma(self):
        try:
            import chromadb
            from chromadb.config import Settings
            self._client = chromadb.PersistentClient(path=str(self.persist_dir))
            # Metadata with cosine space
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine", "embedding_model": self.model_name}
            )
            logger.info(f"Initialized ChromaDB at {self.persist_dir}")
        except Exception as e:
            logger.error(f"Error initializing ChromaDB: {e}")

    def add_chunks(self, chunks: List[Dict[str, Any]], embeddings: np.ndarray):
        if not chunks or self._collection is None:
            return

        ids = [c["chunk_id"] for c in chunks]
        documents = [c["text_content"] for c in chunks]
        metadatas = [{
            "document_id": c["document_id"],
            "page_number": c["page_number"],
            "chunk_index": c.get("chunk_index", 0),
            "collection_name": c.get("collection_name", "General"),
            "filename": c.get("filename", "")
        } for c in chunks]

        # Convert embeddings to python list of floats
        embed_list = embeddings.tolist()

        self._collection.upsert(
            ids=ids,
            embeddings=embed_list,
            documents=documents,
            metadatas=metadatas
        )

    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 5,
        document_filter: Optional[List[str]] = None,
        collection_filter: Optional[str] = None
    ) -> List[Tuple[Dict[str, Any], float]]:
        if self._collection is None or self._collection.count() == 0:
            return []

        where_clause = {}
        if document_filter and len(document_filter) == 1:
            where_clause["document_id"] = document_filter[0]
        if collection_filter and collection_filter != "All":
            where_clause["collection_name"] = collection_filter

        query_list = query_vector.tolist()
        try:
            results = self._collection.query(
                query_embeddings=[query_list],
                n_results=min(top_k, self._collection.count()),
                where=where_clause if where_clause else None
            )

            out: List[Tuple[Dict[str, Any], float]] = []
            if results and results["ids"] and len(results["ids"][0]) > 0:
                for idx in range(len(results["ids"][0])):
                    cid = results["ids"][0][idx]
                    meta = results["metadatas"][0][idx] if results["metadatas"] else {}
                    text = results["documents"][0][idx] if results["documents"] else ""
                    # Chroma returns distance; cosine similarity is 1 - distance
                    dist = results["distances"][0][idx] if results.get("distances") else 0.0
                    sim = max(0.0, 1.0 - dist)

                    chunk_dict = {
                        "chunk_id": cid,
                        "document_id": meta.get("document_id", ""),
                        "page_number": meta.get("page_number", 1),
                        "chunk_index": meta.get("chunk_index", 0),
                        "text_content": text,
                        "collection_name": meta.get("collection_name", "General"),
                        "filename": meta.get("filename", "")
                    }
                    out.append((chunk_dict, float(sim)))
            return out
        except Exception as e:
            logger.error(f"Chroma search error: {e}")
            return []

    def delete_document(self, document_id: str):
        if self._collection:
            try:
                self._collection.delete(where={"document_id": document_id})
                logger.info(f"Deleted document {document_id} from ChromaDB")
            except Exception as e:
                logger.error(f"Chroma delete error: {e}")

    def count(self) -> int:
        return self._collection.count() if self._collection else 0

    def clear(self):
        if self._client:
            try:
                self._client.delete_collection(self.collection_name)
                self._collection = self._client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
            except Exception as e:
                logger.error(f"Chroma clear error: {e}")


def get_vector_store(backend: str = "faiss") -> VectorStoreInterface:
    """Factory method for vector store backend."""
    if backend.lower() == "chroma":
        return ChromaVectorStore()
    return FAISSVectorStore()
