from typing import Annotated, List, Dict, Any, Optional
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class FinanceControllerState(TypedDict):
    """LangGraph state for AI Finance Controller with RBAC attributes."""
    messages: Annotated[List[BaseMessage], add_messages]
    user_id: str
    user_name: Optional[str]
    user_role: str  # CFO, FINANCE_MANAGER, DEPARTMENT_HEAD, AUDITOR
    user_department: Optional[str]  # e.g., "Engineering" for DEPARTMENT_HEAD
    action_type: Optional[str]
    pending_approval: Optional[Dict[str, Any]]
    internal_facts: Annotated[List[Dict[str, Any]], lambda a, b: a + b]
    next: Optional[str]
    suggested_actions: Optional[List[str]]
