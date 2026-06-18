from app.skills.base_skill import BaseSkill, SkillDescriptor
from app.mcp.mcp_client import call_mcp_tool_sync

class MCPJiraSkill(BaseSkill):
    AUTO_REGISTER = True
    
    descriptor = SkillDescriptor(
        name="jira_tool",
        description="Interact with the enterprise Jira MCP server. Allows getting and creating Jira tickets.",
        parameters={
            "action": {"type": "string", "description": "'get' or 'create'"},
            "ticket_id": {"type": "string", "description": "Required for 'get' (e.g., ENG-101)"},
            "title": {"type": "string", "description": "Required for 'create'"},
            "assignee": {"type": "string", "description": "Required for 'create'"}
        },
        tags=["jira", "mcp", "enterprise", "ticketing"]
    )
    
    def execute(self, **kwargs) -> str:
        action = kwargs.get("action")
        if action == "get":
            ticket_id = kwargs.get("ticket_id")
            if not ticket_id:
                return "Error: ticket_id is required for 'get' action."
            return call_mcp_tool_sync("get_jira_ticket", ticket_id=ticket_id)
        elif action == "create":
            title = kwargs.get("title")
            assignee = kwargs.get("assignee")
            if not title or not assignee:
                return "Error: title and assignee are required for 'create' action."
            return call_mcp_tool_sync("create_jira_ticket", title=title, assignee=assignee)
        return "Error: Unknown action. Must be 'get' or 'create'."
