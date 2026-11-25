"""The graph payload (graph-output.md "GraphOut"): Cytoscape's element format (B12).

Settings (colors and shapes) are not part of it (BD31). Full gift card numbers never appear in
it: nodes carry only the masked `display_key` (B13).
"""

import datetime as dt
from typing import Literal

from pydantic import BaseModel

from txnweave_api.schemas.common import DocumentStatus, DocumentType, MatchQuality

EdgeKind = Literal["activated", "used_in", "related"]  # BD6


class NodeData(BaseModel):
    id: str  # equal to document_id
    document_id: str
    node_type: DocumentType
    status: DocumentStatus
    display_key: str  # number, "…1234" for a card, or the Misc name
    date: dt.date | None
    time: str | None
    store_number: str | None
    register_number: str | None  # transactions only
    important: bool  # 4.3


class EdgeData(BaseModel):
    id: str  # e-<kind>-<source>-<target>
    source: str
    target: str
    kind: EdgeKind
    status: DocumentStatus
    match: MatchQuality
    refs: list[str]
    ref_count: int
    important: bool  # 4.4


class CyNode(BaseModel):
    data: NodeData
    classes: str


class CyEdge(BaseModel):
    data: EdgeData
    classes: str


class GraphElements(BaseModel):
    nodes: list[CyNode]
    edges: list[CyEdge]


class GraphCounts(BaseModel):
    nodes: int
    edges: int
    incomplete_nodes: int


class GraphOut(BaseModel):
    investigation_id: int
    generated_at: dt.datetime
    counts: GraphCounts
    elements: GraphElements
