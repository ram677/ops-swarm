from typing import List, Optional, Literal, TypedDict, Annotated
from pydantic import BaseModel, Field
import operator

class IncidentContext(BaseModel):
    """The structured facts of the incident."""
    incident_id: str
    logs: str
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    diagnosis: Optional[str] = None
    proposed_action: Optional[str] = None
    action_status: str = "PENDING"  # PENDING, APPROVED, EXECUTED, REJECTED

class AgentState(TypedDict):
    """The working memory of the graph."""
    # Messages list that grows (chat history)
    messages: Annotated[List[str], operator.add]
    # The structured context object
    context: IncidentContext
    # Signal for Human-in-the-Loop
    require_approval: bool