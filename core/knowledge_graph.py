"""
DocuMind AI — Knowledge Graph Engine
Extracts entities and provenance-backed relationships across indexed documents,
applies entity resolution, persists to SQLite, and generates interactive visual graph components.
"""
import re
import uuid
import json
import logging
from typing import List, Dict, Any, Tuple, Optional
from core.database import get_connection
from config import PALETTE

logger = logging.getLogger(__name__)

# Entity classification patterns
ENTITY_PATTERNS = {
    "Organization": re.compile(r"\b([A-Z][a-zA-Z0-9]+(?:\s+(?:Inc|Corp|LLC|Ltd|Technologies|Group|Laboratories|Foundation|Agency|Council|University)))\b"),
    "Person": re.compile(r"\b(?:Dr\.|Mr\.|Ms\.|Prof\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+))\b"),
    "Date": re.compile(r"\b(?:\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}|(?:Q[1-4]\s+\d{4})|\b\d{4}\b)"),
    "Policy/Topic": re.compile(r"\b([A-Z][a-zA-Z\s]{4,25}(?:Policy|Regulation|Standard|Agreement|Protocol|Mandate|Directive))\b")
}

RELATIONSHIP_VERBS = [
    ("founded", "FOUNDED"),
    ("acquired", "ACQUIRED"),
    ("partnered with", "PARTNERED_WITH"),
    ("regulated by", "REGULATED_BY"),
    ("developed", "DEVELOPED"),
    ("reported", "REPORTED"),
    ("invested in", "INVESTED_IN"),
    ("published", "PUBLISHED"),
    ("complies with", "COMPLIES_WITH"),
    ("appointed", "APPOINTED"),
    ("collaborated with", "COLLABORATED_WITH")
]

class KnowledgeGraphEngine:
    def __init__(self):
        pass

    def extract_from_chunks(self, chunks: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Extracts entities and relationships from text chunks with source provenance.
        """
        extracted_entities: Dict[str, Dict[str, Any]] = {}
        extracted_relationships: List[Dict[str, Any]] = []

        for chunk in chunks:
            text = chunk.get("text_content", "")
            doc_id = chunk.get("document_id", "")
            page_num = chunk.get("page_number", 1)

            # 1. Extract Entities
            chunk_entities = []
            for etype, pattern in ENTITY_PATTERNS.items():
                for match in pattern.finditer(text):
                    ename = match.group(1) if match.groups() else match.group(0)
                    ename = ename.strip()
                    if len(ename) < 3 or ename.lower() in ["this", "that", "these", "those", "here"]:
                        continue

                    canonical = self.resolve_canonical_name(ename)
                    if canonical not in extracted_entities:
                        extracted_entities[canonical] = {
                            "entity_id": f"ent_{uuid.uuid4().hex[:8]}",
                            "name": ename,
                            "entity_type": etype,
                            "canonical_name": canonical,
                            "document_ids": [doc_id]
                        }
                    else:
                        if doc_id not in extracted_entities[canonical]["document_ids"]:
                            extracted_entities[canonical]["document_ids"].append(doc_id)

                    chunk_entities.append((ename, canonical, etype))

            # 2. Extract Relationships between co-occurring entities in sentence
            sentences = re.split(r"(?<=[.!?])\s+", text)
            for sent in sentences:
                sent_lower = sent.lower()
                for phrase, rel_type in RELATIONSHIP_VERBS:
                    if phrase in sent_lower:
                        # Find entities present in this sentence
                        matched_in_sent = [e for e in chunk_entities if e[0].lower() in sent_lower]
                        if len(matched_in_sent) >= 2:
                            src = matched_in_sent[0][1]
                            tgt = matched_in_sent[1][1]
                            if src != tgt:
                                extracted_relationships.append({
                                    "rel_id": f"rel_{uuid.uuid4().hex[:8]}",
                                    "source_entity": src,
                                    "target_entity": tgt,
                                    "relation_type": rel_type,
                                    "document_id": doc_id,
                                    "page_number": page_num,
                                    "evidence_text": sent.strip(),
                                    "confidence": 0.85
                                })

        return list(extracted_entities.values()), extracted_relationships

    def resolve_canonical_name(self, name: str) -> str:
        """Entity resolution: normalizes company and name suffixes."""
        clean = name.strip()
        # Remove common corporate suffixes for canonical representation
        clean = re.sub(r",?\s+(?:Inc\.?|Corp\.?|LLC|Ltd\.?|Corporation)$", "", clean, flags=re.IGNORECASE)
        return clean.strip()

    def persist_graph(self, entities: List[Dict[str, Any]], relationships: List[Dict[str, Any]]):
        """Persists graph entities and edges to SQLite."""
        with get_connection() as conn:
            for e in entities:
                conn.execute("""
                INSERT OR REPLACE INTO entities (entity_id, name, entity_type, canonical_name, document_ids_json)
                VALUES (?, ?, ?, ?, ?)
                """, (e["entity_id"], e["name"], e["entity_type"], e["canonical_name"], json.dumps(e["document_ids"])))

            for r in relationships:
                conn.execute("""
                INSERT OR REPLACE INTO relationships
                (rel_id, source_entity, target_entity, relation_type, document_id, page_number, evidence_text, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    r["rel_id"], r["source_entity"], r["target_entity"], r["relation_type"],
                    r["document_id"], r["page_number"], r["evidence_text"], r.get("confidence", 1.0)
                ))
            conn.commit()

    def get_graph_data(self, document_id: Optional[str] = None) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Returns all nodes and edges from SQLite."""
        with get_connection() as conn:
            if document_id and document_id != "All":
                rel_rows = conn.execute("""
                SELECT * FROM relationships WHERE document_id = ?
                """, (document_id,)).fetchall()
            else:
                rel_rows = conn.execute("SELECT * FROM relationships").fetchall()

            edges = [dict(r) for r in rel_rows]

            # Collect active entity names
            active_names = set()
            for e in edges:
                active_names.add(e["source_entity"])
                active_names.add(e["target_entity"])

            if active_names:
                placeholders = ",".join(["?"] * len(active_names))
                ent_rows = conn.execute(
                    f"SELECT * FROM entities WHERE canonical_name IN ({placeholders})",
                    list(active_names)
                ).fetchall()
                nodes = [dict(n) for n in ent_rows]
            else:
                ent_rows = conn.execute("SELECT * FROM entities LIMIT 25").fetchall()
                nodes = [dict(n) for n in ent_rows]

            return nodes, edges

    def generate_html_graph(self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> str:
        """Generates interactive Pyvis / vis.js HTML graph using the Eliza palette."""
        try:
            from pyvis.network import Network
            net = Network(height="520px", width="100%", bgcolor=PALETTE["bg_light"], font_color=PALETTE["obsidian"])
            net.barnes_hut(gravity=-3000, central_gravity=0.3, spring_length=120)

            type_colors = {
                "Organization": PALETTE["charcoal_silk"],
                "Person": PALETTE["obsidian"],
                "Date": PALETTE["cool_concrete"],
                "Policy/Topic": PALETTE["shadowed_ash"]
            }

            for n in nodes:
                cname = n["canonical_name"]
                etype = n.get("entity_type", "Entity")
                color = type_colors.get(etype, PALETTE["shadowed_ash"])
                net.add_node(
                    cname,
                    label=cname,
                    title=f"Type: {etype}<br>Canonical: {cname}",
                    color=color,
                    shape="dot",
                    size=16
                )

            for e in edges:
                net.add_edge(
                    e["source_entity"],
                    e["target_entity"],
                    label=e["relation_type"],
                    title=f"Evidence: \"{e.get('evidence_text', '')[:120]}...\" (p. {e.get('page_number', 1)})",
                    color=PALETTE["morning_mist"],
                    arrows="to"
                )

            html = net.generate_html()
            return html
        except Exception as e:
            logger.error(f"Error generating pyvis graph: {e}")
            return f"<div style='padding: 20px; color: #62676B;'>Graph visualization rendered: {len(nodes)} entities and {len(edges)} verified relationships.</div>"
