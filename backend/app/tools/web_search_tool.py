from app.tools.base_tool import BaseTool
import json
try:
    from ddgs import DDGS
    HAS_DDGS = True
except ImportError:
    HAS_DDGS = False

class WebSearchTool(BaseTool):
    """Real web search using DuckDuckGo."""

    def execute(self, query: str) -> str:
        if not HAS_DDGS:
            return "Error: duckduckgo-search package is not installed."
        
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=5))
                
                if not results:
                    return f"No search results found for: {query}"
                    
                formatted_results = []
                for idx, r in enumerate(results, 1):
                    formatted_results.append(f"{idx}. {r.get('title')}\nURL: {r.get('href')}\nSummary: {r.get('body')}\n")
                    
                return "\n".join(formatted_results)
        except Exception as e:
            return f"Web search failed: {str(e)}"
