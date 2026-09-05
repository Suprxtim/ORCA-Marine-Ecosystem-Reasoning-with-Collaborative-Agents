import operator
from typing import Annotated, Sequence, TypedDict

from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    """
    The state of the multi-agent graph.
    - messages: Tracks the conversation history and intermediate tool outputs.
    - next: The name of the next agent to route to, or 'FINISH' if complete.
    - layers: Generated GeoJSON layers for visualization on the map.
    - target_language: The selected language for the final output (e.g. English, Hindi).
    """
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str
    layers: list[dict]
    target_language: str
