import httpx

from app.tools.base_tool import BaseTool


class WebSearchTool(BaseTool):

    def execute(self, query: str):

        return (
            f"Web search placeholder: {query}"
        )
