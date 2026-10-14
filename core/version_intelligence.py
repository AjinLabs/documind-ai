"""
DocuMind AI — Document Version Intelligence Engine
Tracks document versions, detects duplicates, executes deterministic diffs,
and highlights changed clauses, numerical values, and effective dates across revisions.
"""
import difflib
import re
import uuid
import json
import logging
from typing import List, Dict, Any, Tuple

from core.database import get_connection

logger = logging.getLogger(__name__)

class VersionIntelligenceEngine:
    def __init__(self):
        pass

    def compare_documents(
        self,
        doc_a_chunks: List[Dict[str, Any]],
        doc_b_chunks: List[Dict[str, Any]],
        doc_a_name: str = "Version A",
        doc_b_name: str = "Version B"
    ) -> Dict[str, Any]:
        """
        Executes deterministic diff analysis between two document chunk sets.
        Detects additions, deletions, modified clauses, and numerical value shifts.
        """
        text_a_lines = []
        for c in doc_a_chunks:
            p = c.get("page_number", 1)
            for line in c.get("text_content", "").splitlines():
                if line.strip():
                    text_a_lines.append(f"[p.{p}] {line.strip()}")

        text_b_lines = []
        for c in doc_b_chunks:
            p = c.get("page_number", 1)
            for line in c.get("text_content", "").splitlines():
                if line.strip():
                    text_b_lines.append(f"[p.{p}] {line.strip()}")

        # Deterministic unified diff
        diff_lines = list(difflib.unified_diff(
            text_a_lines,
            text_b_lines,
            fromfile=doc_a_name,
            tofile=doc_b_name,
            lineterm=""
        ))

        additions = [l[1:].strip() for l in diff_lines if l.startswith("+") and not l.startswith("+++")]
        deletions = [l[1:].strip() for l in diff_lines if l.startswith("-") and not l.startswith("---")]

        # Numerical & Date Shifts
        num_pattern = re.compile(r"\b\d+[\.,]?\d*\b")
        date_pattern = re.compile(r"\b(?:\d{4}|\d{1,2}/\d{1,2}/\d{2,4})\b")

        changed_figures = []
        for d in deletions[:20]:
            nums_d = set(num_pattern.findall(d))
            for a in additions[:20]:
                nums_a = set(num_pattern.findall(a))
                if nums_d and nums_a and nums_d != nums_a:
                    changed_figures.append({
                        "previous_clause": d,
                        "updated_clause": a,
                        "old_figures": list(nums_d),
                        "new_figures": list(nums_a)
                    })

        # Calculate similarity ratio
        seq_matcher = difflib.SequenceMatcher(None, "\n".join(text_a_lines), "\n".join(text_b_lines))
        similarity_ratio = round(seq_matcher.ratio() * 100, 1)

        summary = {
            "similarity_percentage": similarity_ratio,
            "additions_count": len(additions),
            "deletions_count": len(deletions),
            "changed_figures_count": len(changed_figures),
            "sample_additions": additions[:5],
            "sample_deletions": deletions[:5],
            "changed_figures": changed_figures[:5],
            "diff_text": "\n".join(diff_lines[:120])
        }

        return summary
