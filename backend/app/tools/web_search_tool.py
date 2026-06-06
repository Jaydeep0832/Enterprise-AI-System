from app.tools.base_tool import BaseTool


class WebSearchTool(BaseTool):
    """Placeholder — will be replaced with Tavily or Brave Search API later."""

    def execute(self, query: str):
        # TODO: integrate a real search API
        return f"Web search placeholder: {query}"
