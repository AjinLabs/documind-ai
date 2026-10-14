"""
DocuMind AI — Evidence & Contradiction Intelligence Engine
Identifies factual claims across indexed documents, flags potential contradictions,
pairs conflicting evidence side-by-side with page provenance, and maintains a reviewer ledger.
"""
import re
import uuid
import logging
from typing import List, Dict, Any, Optional
from core.database import get_connection

logger = logging.getLogger(__name__)

class EvidenceEngine:
    def __init__(self):
        pass

    def extract_claims_from_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extracts atomic claims containing factual assertions, numbers, dates, or obligations.
        """
        claims = []
        fact_patterns = [
            re.compile(r"\b(shall|must|will|agreed|declined|increased|decreased|totaled|reported|achieved)\b", re.IGNORECASE),
            re.compile(r"\b(\d{4}|\d+[\.,]?\d*\s*%)", re.IGNORECASE),
            re.compile(r"\b(revenue|profit|loss|liability|deadline|effective date|penalty)\b", re.IGNORECASE)
        ]

        for chunk in chunks:
            doc_id = chunk.get("document_id", "")
            page_num = chunk.get("page_number", 1)
            text = chunk.get("text_content", "")
            sentences = re.split(r"(?<=[.!?])\s+", text)

            for sent in sentences:
                sent = sent.strip()
                if len(sent) < 25 or len(sent) > 300:
                    continue

                # Match if sentence contains factual/numerical indicators
                matches = sum(1 for p in fact_patterns if p.search(sent))
                if matches >= 1:
                    claim_id = f"clm_{uuid.uuid4().hex[:8]}"
                    claims.append({
                        "claim_id": claim_id,
                        "claim_text": sent,
                        "document_id": doc_id,
                        "page_number": page_num,
                        "supporting_excerpt": sent,
                        "verification_status": "requires_human_review",
                        "related_claims_json": "[]",
                        "contradictions_json": "[]",
                        "reviewer_notes": ""
                    })

        return claims

    def detect_cross_contradictions(self, claims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Cross-compares claims across different documents to identify potential contradictions
        (e.g., opposing numeric values, conflicting dates, antonymic verbs).
        """
        analyzed_claims = []
        # Group by topic or shared keywords
        for i, c1 in enumerate(claims):
            c1_copy = dict(c1)
            text1 = c1["claim_text"].lower()
            words1 = set(re.findall(r"\w{4,}", text1))
            contradictions = []

            for j, c2 in enumerate(claims):
                if i == j or c1["document_id"] == c2["document_id"]:
                    continue

                text2 = c2["claim_text"].lower()
                words2 = set(re.findall(r"\w{4,}", text2))
                overlap = words1.intersection(words2)

                # If they share context words (at least 2 common significant terms)
                opposing_pairs = [
                    ("increase", "decrease"), ("rise", "fall"), ("profit", "loss"),
                    ("approved", "rejected"), ("exceeded", "fell short"), ("complied", "violated")
                ]
                has_opposing = any(
                    (p[0] in text1 and p[1] in text2) or (p[1] in text1 and p[0] in text2)
                    for p in opposing_pairs
                )
                # Check for conflicting numbers
                nums1 = re.findall(r"\b\d+[\.,]?\d*\b", text1)
                nums2 = re.findall(r"\b\d+[\.,]?\d*\b", text2)
                has_different_nums = bool(nums1 and nums2 and set(nums1) != set(nums2))

                if (len(overlap) >= 2 or has_opposing) and (has_opposing or has_different_nums):
                        contradictions.append({
                            "contradicting_claim_id": c2["claim_id"],
                            "document_id": c2["document_id"],
                            "page_number": c2["page_number"],
                            "passage": c2["claim_text"],
                            "reason": "Opposing directional assertions or conflicting numerical figures."
                        })

            if contradictions:
                c1_copy["verification_status"] = "potentially_contradicted"
                c1_copy["contradictions"] = contradictions
            else:
                c1_copy["verification_status"] = "supported"
                c1_copy["contradictions"] = []

            analyzed_claims.append(c1_copy)

        return analyzed_claims

    def save_claims(self, claims: List[Dict[str, Any]]):
        """Persists analyzed claims to SQLite."""
        import json
        with get_connection() as conn:
            for c in claims:
                conn.execute("""
                INSERT OR REPLACE INTO claims
                (claim_id, claim_text, document_id, page_number, supporting_excerpt, verification_status, related_claims_json, contradictions_json, reviewer_notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    c["claim_id"],
                    c["claim_text"],
                    c["document_id"],
                    c["page_number"],
                    c["supporting_excerpt"],
                    c.get("verification_status", "requires_human_review"),
                    json.dumps(c.get("related_claims", [])),
                    json.dumps(c.get("contradictions", [])),
                    c.get("reviewer_notes", "")
                ))
            conn.commit()

    def get_all_claims(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves stored claims from SQLite with document filenames."""
        import json
        with get_connection() as conn:
            if status_filter and status_filter != "All":
                rows = conn.execute("""
                SELECT c.*, d.filename
                FROM claims c
                LEFT JOIN documents d ON c.document_id = d.document_id
                WHERE c.verification_status = ?
                ORDER BY c.created_at DESC
                """, (status_filter,)).fetchall()
            else:
                rows = conn.execute("""
                SELECT c.*, d.filename
                FROM claims c
                LEFT JOIN documents d ON c.document_id = d.document_id
                ORDER BY c.created_at DESC
                """).fetchall()

            results = []
            for r in rows:
                d = dict(r)
                d["contradictions"] = json.loads(d["contradictions_json"]) if d.get("contradictions_json") else []
                d["related_claims"] = json.loads(d["related_claims_json"]) if d.get("related_claims_json") else []
                results.append(d)
            return results

    def update_reviewer_status(self, claim_id: str, new_status: str, notes: str):
        """Updates claim verification status and reviewer audit notes."""
        with get_connection() as conn:
            conn.execute("""
            UPDATE claims
            SET verification_status = ?, reviewer_notes = ?
            WHERE claim_id = ?
            """, (new_status, notes, claim_id))
            conn.commit()
