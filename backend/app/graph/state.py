from typing import TypedDict
from typing import List


class AgentState(TypedDict):

    query: str

    result: str

    route: str

    history: List[str]
