# Enterprise AI System

Hey there! 👋 Welcome to the Enterprise AI System.

This project is a robust, multi-agent RAG (Retrieval-Augmented Generation) application designed for enterprise environments. Rather than just a simple chatbot, this system uses specialized agents to handle complex workflows, retain long-term memory, and securely connect to external tools via the Model Context Protocol (MCP).

## What it does

- **Smart Document Processing:** Upload your PDFs, text files, and markdown docs. We automatically chunk, embed, and store them securely using PostgreSQL (`pgvector`).
- **Hybrid Search:** When you ask a question, the backend uses a combination of semantic (vector) search and keyword search to find the exact paragraphs that matter.
- **Traceable Answers:** The UI doesn't just give you an answer; it shows you exactly *which* document and chunk the AI used to formulate its response.
- **Persistent Memory:** It remembers your past conversations and user preferences using Redis. Switch between different chat sessions seamlessly from the sidebar.
- **MCP Integration:** We've built in a Model Context Protocol client so the AI can securely interact with enterprise tools (like creating Jira tickets) without hardcoding integrations.

## Tech Stack

- **Frontend:** React, Vite, Tailwind CSS, Framer Motion (for a sleek, dark-mode glassmorphism UI).
- **Backend:** FastAPI (Python), LangGraph (for multi-agent orchestration).
- **Database & Storage:** PostgreSQL with `pgvector` for documents, Redis for conversation history and fast caching.
- **Containerization:** Fully Dockerized for easy deployment.

## Getting Started

1. **Spin up the databases:** Run `docker-compose up -d` to get PostgreSQL and Redis running.
2. **Start the backend:** Make sure your virtual environment is active, then run `uvicorn app.main:app --reload` from the `backend/` directory.
3. **Start the frontend:** Head into the `frontend/` folder and run `npm run dev`.
4. Drop a document into the UI and start chatting!

Feel free to open an issue or submit a pull request if you want to contribute!