# Implementation Log — Enterprise AI System

> my running notes on what i built, what broke, and how i fixed it.
> whenever i come back to this project after a break, i read this file first.

---

## what this project is

building an enterprise-grade AI system from scratch to learn how modern AI platforms work.
not a toy chatbot — a real multi-agent system with RAG, memory, tool calling, and observability.

| thing | detail |
|---|---|
| stack | FastAPI + React + PostgreSQL/pgvector + Redis + LangGraph |
| agents | router, tool, rag, research — with LLM failover (gemini → groq → openrouter → openai) |
| repo | [github.com/Jaydeep0832/Enterprise-AI-System](https://github.com/Jaydeep0832/Enterprise-AI-System) |

---

## how the system flows

```
browser → react frontend
  → POST /api/v1/chat { question, session_id }
  → FastAPI backend
    → LangGraph workflow:
      1. load_memory (pull history from redis)
      2. router_node (decide: math? rag? research?)
      3. agent_node (tool/rag/research agent does the work)
      4. save_memory (store Q&A back to redis)
  → response back to frontend
```

the RAG pipeline is separate:
```
PDF upload → pypdf extract → chunk (500 chars, 50 overlap) → embed (MiniLM-L6-v2, 384d) → pgvector
query → embed → cosine search → top-5 chunks → stuff into LLM prompt → answer
```

---

## phase 1-3: initial build

built the whole thing out in about two weeks. got the basic flow working:
- fastapi backend with versioned api routes
- react chat ui with pdf upload
- multi-agent setup: router decides where to send queries
- langgraph stategraph for agent orchestration
- llm failover across 4 providers
- rag pipeline for document Q&A
- redis for session memory
- 27 test scripts

seemed solid. then i actually looked at it carefully...

---

## phase 4: the audit (june 4, 2026)

sat down and traced every import chain, every method call, every api route.
found 25 issues. 4 of them were critical. here's the damage:

### bug 1: rag agent calls a method that doesn't exist

```python
# rag_agent.py was doing:
return self.rag.ask(question)
# but RAGService only has .answer(), not .ask()
# so /api/v1/rag would crash with AttributeError every single time
```

simple fix, but embarrassing. taught me to always check method signatures at the call site.

### bug 2: eval() in the calculator — remote code execution

```python
# calculator_tool.py was doing:
return eval(expression)
# meaning someone could send: __import__('os').system('rm -rf /')
# as a "math expression" and it would execute on my server
```

this is a classic security anti-pattern. even in a learning project, it's a bad habit.
fixed it with AST-based parsing — only allows numbers and basic math operators.

### bug 3: all users share the same memory

```python
# conversation_memory.py had a module-level singleton:
memory = ConversationMemory()
# every agent imported this same object
# so user A would see user B's conversation
```

works fine when you're the only user. falls apart immediately in production.
fixed by using RedisMemory with session IDs in the actual chat flow.

### bug 4: the chat api ignores the entire agent architecture

```python
# chat.py was doing:
rag = RAGService()
answer = rag.answer(request.question)
# bypassing RouterAgent, LangGraph, memory, everything.
# all that agent code? dead code.
```

the langgraph workflow existed and worked — it just wasn't used anywhere.
i wired it into the chat endpoint so everything actually runs through the graph now.

### other findings

- memory_node.py calls `get_history()` but the class only has `get_context()` — crashes
- save_memory_node.py calls `add_message(text)` but the class has `add(role, content)` — crashes  
- two ingestion services doing the same thing (raw sql vs orm)
- requirements.txt only has 15 of 90+ packages
- SentenceTransformer model loads 4 separate times on startup (~30s)
- web search tool is a placeholder returning hardcoded strings
- dead code everywhere: provider_manager.py, orchestrator.py, state.py — never used

### lesson: i should have audited before building more features

i was about to start working on the document upload pipeline when i decided to audit first.
glad i did. building new features on a broken foundation just creates more broken features.

---

## phase 5: roadmap (june 4, 2026)

after the audit, planned out phases 6-10:

| phase | what | weeks |
|---|---|---|
| 6 | fix all bugs, wire everything together, complete doc pipeline | 2-3 |
| 7 | agent planner/executor, skills framework, real tool implementations | 3-4 |
| 8 | hybrid search (bm25 + vector), multi-tier memory, MCP server | 4-5 |
| 9 | observability (langsmith/phoenix), rag evaluation (ragas), feedback loop | 3-4 |
| 10 | knowledge graph (neo4j), workflow builder, multi-agent collab, deployment | 5-6 |

key decision: fix before build. phase 6 is entirely about stabilization.

---

## phase 6: fixing everything (june 6, 2026)

### 6.1 — fixed rag agent method name

changed `self.rag.ask()` to `self.rag.answer()`. one line. five minutes.
also fixed the same bug in `langgraph_workflow.py` where `rag_node` was calling `.ask()`.

### 6.2 — replaced eval() with safe math parser

built an AST-based evaluator that only allows arithmetic:
- parse the expression into an AST tree
- walk the tree node by node
- only evaluate nodes that match allowed operators (+, -, *, /, **, %)
- reject everything else (function calls, imports, attribute access)

tested with: `2 + 3`, `10 * (5 - 2)`, `2 ** 8`, `-42`  
tried the exploit: `__import__('os').system('ls')` → properly rejected.

### 6.3 — connected langgraph to the chat api

before: `chat.py` created its own `RAGService()` and called it directly.
after: `chat.py` calls `graph.invoke()` which runs the full pipeline.

flow now: `load_memory → router → tool/rag/research → save_memory → END`

### 6.4 — added session support

- added `session_id` field to `ChatRequest` (optional, auto-generated if missing)
- added `session_id` to `ChatResponse` so frontend can track it
- frontend stores the session id and sends it with every message
- each session has its own redis conversation history

### 6.5 — fixed memory nodes

rewrote both `memory_node.py` and `save_memory_node.py`:
- switched from ConversationMemory singleton to RedisMemory
- fixed all method names to match the actual interface
- wired them into the langgraph: load_memory at start, save_memory at end

### 6.6 — made embedder a singleton

the SentenceTransformer model was loading 4 times on startup (once per service that uses it).
made Embedder use `__new__()` to return the same instance every time.
startup went from ~30s to ~8s.

### 6.x — code cleanup

went through every file and cleaned up formatting:
- removed excessive blank lines between statements
- consolidated imports
- removed unused imports (httpx in web_search_tool)
- refactored LLMService to extract duplicate chat-completion code
- refactored ToolAgent to extract chain operation logic
- made code style consistent across the whole backend

---

## what's left in phase 6

| task | status |
|---|---|
| document upload with metadata + management api | not started |
| regenerate requirements.txt from venv | not started |
| remove dead code files | not started |
| convert test scripts to pytest | not started |
| add alembic migrations | not started |
| dockerfile + docker-compose | not started |

---

## common errors i hit (quick reference)

| error | what happened | fix |
|---|---|---|
| `AttributeError: no attribute 'ask'` | method name mismatch between rag_agent and rag_service | check method names match at call sites |
| `eval()` code execution | user input passed directly to eval | use ast-based safe parser |
| memory leaking between users | module-level singleton shared across requests | per-session instances with redis |
| model loads 4x on startup | every service creates its own Embedder() | singleton pattern for heavy models |
| langgraph not actually used | chat api bypassed the graph entirely | route everything through graph.invoke() |
| `get_history()` doesn't exist | wrong method name on ConversationMemory | use `get_context()` (the actual method) |
| `add_message(text)` doesn't exist | wrong signature on ConversationMemory | use `add(role, content)` |
| project name collision | pyproject.toml named "langchain" conflicts with the langchain package | renamed to "enterprise-ai-system" |
| requirements.txt incomplete | only 15 of 90+ deps listed | need to regenerate from venv |

---

## key files i keep coming back to

| file | what it does |
|---|---|
| `backend/app/main.py` | fastapi entry point, route registration |
| `backend/app/api/v1/chat.py` | main chat endpoint — invokes langgraph |
| `backend/app/graph/langgraph_workflow.py` | the actual agent graph |
| `backend/app/services/llm_service.py` | llm provider failover chain |
| `backend/app/rag/rag_service.py` | retrieve + prompt + generate |
| `backend/app/rag/embedder.py` | singleton sentence-transformers embedder |
| `backend/app/memory/redis_memory.py` | per-session memory in redis |
| `backend/app/tools/calculator_tool.py` | safe math evaluator |
| `frontend/src/App.tsx` | react chat ui with file upload |

---

*last updated: june 10, 2026*

---

## phase 6 completion (june 10, 2026)

### 6.7 — complete document upload pipeline

upgraded the entire ingestion stack:

**new capabilities:**
- multi-format support: PDF, TXT, MD, DOCX (uses python-docx)
- metadata stored per chunk: filename, file_type, chunk_index, total_chunks, uploaded_at
- document management API:
  - `GET /documents` — list all docs grouped by filename with chunk count
  - `GET /documents/{id}` — retrieve a specific chunk by DB id
  - `DELETE /documents/{filename}` — delete all chunks for a file (also removes from disk)
- unsupported file types return 400 with a clear error message

**what i learned:** storing metadata alongside embeddings is critical for document management. without filename + chunk_index, you can't list, filter, or delete documents.

### 6.8 — requirements.txt regenerated

ran `pip freeze > requirements.txt` — went from 15 packages to 125.
the old file was generated manually at the start. never do that — always freeze from the actual venv.

### 6.9 — dead code removed

deleted 3 files that were never imported:
- `graph/orchestrator.py` — replaced by LangGraph
- `graph/state.py` — TypedDict defined inline in langgraph_workflow.py
- `rag/ingestion.py` — duplicate of document_ingestion.py but using raw SQL

### 6.10 — pytest test suite (41 total tests)

converted 27 manual test scripts into a proper pytest suite:

| file | tests | what it covers |
|---|---|---|
| `test_calculator.py` | 13 | arithmetic, edge cases, security exploits |
| `test_health.py` | 6 | endpoint, db connection, redis connection |
| `test_memory.py` | 5 | add/retrieve, session isolation, clear, API |
| `test_upload.py` | 9 | PDF/TXT/MD upload, type rejection, list, delete |
| `test_chat.py` | 8 | chat routing, LLM calls, session, RAG, research |

run from backend/ dir: `python -m pytest ../tests/ -v`

**lesson:** tests that import the FastAPI app must be run from the directory that contains `.env`. pydantic-settings finds `.env` relative to the working directory, not the script location.

### 6.11 — alembic migrations

set up alembic properly:
- `alembic init alembic` in backend/
- configured `env.py` to import our settings (DB URL from .env)
- pointed `target_metadata` at `Document.Base.metadata` for autogenerate
- generated initial migration: added 5 metadata columns to documents table
- fixed the migration to add columns as nullable → backfill defaults → set NOT NULL (handles existing rows safely)
- `alembic upgrade head` — all migrations applied

### 6.12 — dockerfile + docker-compose

- `backend/Dockerfile` — Python 3.11-slim, installs all requirements, runs uvicorn
- `frontend/Dockerfile` — multi-stage: Node 20 builds React, nginx serves the dist
- `docker-compose.yml` — 4 services:
  - `postgres` (pgvector/pgvector:pg16) with health check
  - `redis` (redis:7-alpine) with health check
  - `backend` — depends_on postgres+redis health checks
  - `frontend` — nginx with SPA routing + API proxy to backend

### other fixes in this session

- `history.py` — was returning shared in-memory singleton. now uses `RedisMemory(session_id)` for per-session history. added DELETE endpoint.
- `base_agent.py` — removed the `self.memory = memory` singleton. agents are now stateless — memory is managed by the LangGraph nodes only.
- `tool_agent.py` — removed singleton memory dependency, uses instance-level `_last_result` for chaining
- `langgraph_workflow.py` — expanded router keywords (added: calculate, compute, pdf, file, according to)

### test results

```
33 passed (health + memory + upload + calculator) — 0 failures
 8 passed (chat integration with real LLM calls) — 0 failures
─────────────────────────────────────────────────────
41 total tests passing
```

## what's left (phase 7)

| milestone | what |
|---|---|
| 7.1 | Skills Framework (descriptors, registry, dynamic loading) |
| 7.2 | Real web search tool (Tavily or Brave API) |
| 7.3 | File read/summarize tools |
| 7.4 | Agent Executor with iterative tool-use loop |
| 7.5 | Agent Planner with task decomposition |
| 7.6 | Integrate planner + executor in LangGraph |
| 7.7 | Safety guardrails (max iterations, budget) |
| 7.8 | Agent execution tracing |
| 7.9 | Brainstorming Agent |
| 7.10 | Frontend: agent status display |

