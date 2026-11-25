"""The graph (graph-output.md section 4): saved documents, placeholders and merged links become
Cytoscape nodes and edges (B12).

`build_graph` is pure (G5): it takes the output of relationship resolution and touches no
database. `get_graph` is the thin wrapper the route calls.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from txnweave_api.schemas.documents import AnyDocumentOut, GiftCardOut, OnlineOrderOut, TransactionOut
from txnweave_api.schemas.graph import (
    CyEdge,
    CyNode,
    EdgeData,
    EdgeKind,
    GraphCounts,
    GraphElements,
    GraphOut,
    NodeData,
)
from txnweave_api.services import document_service
from txnweave_api.services.relationship_service import Link, Resolution, resolve

# Cytoscape class names use dashes (graph-output.md "Classes").
_TYPE_CLASS = {"transaction": "transaction", "gift_card": "gift-card", "online_order": "online-order", "misc": "misc"}
_KIND_CLASS = {"activated": "activated", "used_in": "used-in", "related": "related"}


# ---- Nodes ----


def _node(doc: AnyDocumentOut) -> CyNode:
    """One node per document or placeholder (4.1). The masked card number is the only form of
    it that ever goes into the graph (B13)."""
    register = None
    if isinstance(doc, TransactionOut):
        key, on, at, store, register = doc.transaction_number, doc.date, doc.time, doc.store_number, doc.register_number
    elif isinstance(doc, GiftCardOut):
        activation = doc.activation
        key = f"…{(doc.gift_card_number or '')[-4:]}"
        on, at, store = (activation.date, activation.time, activation.store_number) if activation else (None, None, None)
    elif isinstance(doc, OnlineOrderOut):
        key, on, at, store = doc.order_number, doc.placed_date, doc.placed_time, doc.pickup_store_number
    else:  # Misc
        key, on, at, store = doc.name, doc.date, doc.time, None

    important = doc.important and doc.status == "complete"  # placeholders are never important (4.3)
    classes = [_TYPE_CLASS[doc.type]]
    if doc.status == "incomplete":
        classes.append("incomplete")
    elif important:
        classes.append("important")

    data = NodeData(
        id=doc.id,
        document_id=doc.id,
        node_type=doc.type,
        status=doc.status,
        display_key=key or "",
        date=on,
        time=at,
        store_number=store,
        register_number=register,
        important=important,
    )
    return CyNode(data=data, classes=" ".join(classes))


# ---- Edges ----


def _edge_ends(link: Link) -> tuple[str, str]:
    """Edge direction follows table 3.2, which isn't always the reference's own direction.
    A link says "source references target". Two rules point the edge the other way:
    an activation (R1) is drawn Transaction → Gift Card, and a gift card payment row
    (R2b, R3, R4) is drawn Gift Card → the document that paid with it."""
    if link.kind == "activated" or link.ref == "payment":
        return link.target_id, link.source_id
    return link.source_id, link.target_id


@dataclass
class _MergedEdge:
    source: str
    target: str
    kind: EdgeKind
    refs: set[str] = field(default_factory=set)
    ref_count: int = 0
    any_exact: bool = False


def _merge(links: Sequence[Link]) -> list[_MergedEdge]:
    """3.9: links with the same (source, target, kind) become one edge."""
    merged: dict[tuple[str, str, str], _MergedEdge] = {}
    for link in links:
        source, target = _edge_ends(link)
        edge = merged.setdefault((source, target, link.kind), _MergedEdge(source, target, link.kind))
        edge.refs.add(link.ref)
        edge.ref_count += 1
        edge.any_exact = edge.any_exact or link.match == "exact"
    return list(merged.values())


def _edge(merged: _MergedEdge, nodes: dict[str, NodeData]) -> CyEdge:
    source, target = nodes[merged.source], nodes[merged.target]
    match = "exact" if merged.any_exact else "ambiguous"
    # 3.10: incomplete if either end is a placeholder or the match is ambiguous (B5, BD15).
    incomplete = source.status == "incomplete" or target.status == "incomplete" or match == "ambiguous"
    important = source.important and target.important  # 4.4, worked out on every call

    classes = [_KIND_CLASS[merged.kind]]
    if incomplete:
        classes.append("incomplete")
    if match == "ambiguous":
        classes.append("ambiguous")
    if important:
        classes.append("important")

    data = EdgeData(
        id=f"e-{merged.kind}-{merged.source}-{merged.target}",
        source=merged.source,
        target=merged.target,
        kind=merged.kind,
        status="incomplete" if incomplete else "complete",
        match=match,
        refs=sorted(merged.refs),
        ref_count=merged.ref_count,
        important=important,
    )
    return CyEdge(data=data, classes=" ".join(classes))


# ---- The whole graph ----


def build_graph(
    investigation_id: int,
    saved: Sequence[AnyDocumentOut],
    resolution: Resolution,
    generated_at: datetime,
) -> GraphOut:
    """Pure. The same input always gives the same elements (3.12)."""
    documents = sorted([*saved, *resolution.placeholders], key=document_service.document_order)
    nodes = [_node(doc) for doc in documents]
    node_data = {node.data.id: node.data for node in nodes}
    edges = sorted((_edge(m, node_data) for m in _merge(resolution.links)), key=lambda edge: edge.data.id)

    return GraphOut(
        investigation_id=investigation_id,
        generated_at=generated_at,
        counts=GraphCounts(
            nodes=len(nodes),
            edges=len(edges),
            incomplete_nodes=sum(1 for node in nodes if node.data.status == "incomplete"),
        ),
        elements=GraphElements(nodes=nodes, edges=edges),
    )


def get_graph(session: Session, investigation_id: int) -> GraphOut:
    """GET .../graph. 404 if the investigation doesn't exist; 200 with empty lists if it has
    no documents (4.2)."""
    saved = document_service.saved_documents(session, investigation_id)
    return build_graph(investigation_id, saved, resolve(investigation_id, saved), datetime.now(timezone.utc))
