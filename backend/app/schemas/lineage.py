from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class LineageNodeSchema(BaseModel):
    id: int
    name: str
    type: str
    metadata: Optional[Dict[str, Any]] = None

class LineageEdgeSchema(BaseModel):
    source_id: int
    target_id: int
    label: Optional[str] = None

class LineageSchema(BaseModel):
    nodes: List[LineageNodeSchema]
    edges: List[LineageEdgeSchema]
