"""Investigation settings schemas (data-model.md "Investigation settings", BD29).

Colors are palette token names, never hex. `InvestigationSettingsIn` is a full replacement:
all four type styles and the edge color are required.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict

NodeColorToken = Literal["ink", "slate", "mist", "rose", "crimson"]
# Rose and mist fail 3:1 against the mist canvas, so they can't be edge colors (D27).
EdgeColorToken = Literal["ink", "slate", "crimson"]
NodeShape = Literal["ellipse", "rectangle", "round-rectangle", "triangle", "diamond", "hexagon", "octagon", "star"]

# The four document types, in display order.
DOCUMENT_TYPES = ("transaction", "gift_card", "online_order", "misc")


class TypeStyle(BaseModel):
    model_config = ConfigDict(extra="forbid")
    color: NodeColorToken
    shape: NodeShape


class NodeStyles(BaseModel):
    model_config = ConfigDict(extra="forbid")
    transaction: TypeStyle
    gift_card: TypeStyle
    online_order: TypeStyle
    misc: TypeStyle


class InvestigationSettingsIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    node_styles: NodeStyles
    important_edge_color: EdgeColorToken


class InvestigationSettingsOut(InvestigationSettingsIn):
    is_default: bool  # true when the effective values equal the defaults


# D9's styles, with ink as the important-edge color (BD29).
DEFAULT_SETTINGS = InvestigationSettingsIn(
    node_styles=NodeStyles(
        transaction=TypeStyle(color="slate", shape="ellipse"),
        gift_card=TypeStyle(color="crimson", shape="round-rectangle"),
        online_order=TypeStyle(color="ink", shape="hexagon"),
        misc=TypeStyle(color="rose", shape="diamond"),
    ),
    important_edge_color="ink",
)
