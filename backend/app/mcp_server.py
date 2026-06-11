import json
import uuid
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("EnterpriseJiraMock")

# Mock database for Jira tickets
TICKETS = {
    "ENG-101": {"title": "Update Postgres to v15", "status": "In Progress", "assignee": "Alice"},
    "ENG-102": {"title": "Fix RAG pipeline bug", "status": "Open", "assignee": "Bob"}
}

@mcp.tool()
def get_jira_ticket(ticket_id: str) -> str:
    """Fetch details of a Jira ticket by its ID (e.g., ENG-101)."""
    ticket = TICKETS.get(ticket_id.upper())
    if ticket:
        return json.dumps({"ticket_id": ticket_id.upper(), **ticket})
    return f"Ticket {ticket_id} not found."

@mcp.tool()
def create_jira_ticket(title: str, assignee: str) -> str:
    """Create a new Jira ticket with a title and assignee."""
    new_id = f"ENG-{100 + len(TICKETS) + 1}"
    TICKETS[new_id] = {
        "title": title,
        "status": "Open",
        "assignee": assignee
    }
    return f"Successfully created ticket {new_id}."

if __name__ == "__main__":
    # Run via stdio by default. For SSE, use mcp.run(transport='sse')
    mcp.run()
