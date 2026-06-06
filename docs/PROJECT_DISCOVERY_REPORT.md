# Enterprise AI System — Project Discovery Report

> **Date:** 2026-06-04  
> **Analyst:** Senior AI Systems Architect  
> **Phase:** 2 — Project Understanding

---

## 1. Project Overview

The Enterprise AI System is an **educational and research-driven** project built to learn and implement modern AI system architecture concepts through hands-on practice. It is NOT a production chatbot — it is a structured learning platform where each feature teaches a real AI engineering pattern.

| Attribute | Value |
|---|---|
| **Repository** | [github.com/Jaydeep0832/Enterprise-AI-System](https://github.com/Jaydeep0832/Enterprise-AI-System) |
| **Branch** | `main` |
| **Commits** | 3 (Initial commit → Initial architecture → merge conflict fix) |
| **License** | MIT |
| **Status** | Active development (Phase 5.x complete, Phase 6.1 in progress) |

### Core Learning Goals
- Multi-Agent Systems & Agent Orchestration
- RAG (Retrieval Augmented Generation)
- MCP (Model Context Protocol)
- LangGraph Workflows
- LLM Failover Strategies
- Vector Databases (pgvector)
- Memory Systems (Redis + in-memory)
- Tool Calling & Skills Architecture
- Production AI Engineering Patterns

---

## 2. Architecture Overview

```
Frontend (React + TypeScript + Tailwind v4 + Vite)
         │
         ▼
   FastAPI Backend (Python 3.12)
         │
         ├─── API Layer (/api/v1/)
         │       ├── /health
         │       ├── /chat
         │       ├── /rag
         │       ├── /research
         │       ├── /history
         │       └── /upload
         │
         ├─── Agent Layer
         │       ├── RouterAgent (keyword-based routing)
         │       ├── ToolAgent (calculator + web search)
         │       ├── RAGAgent (vector-based QA)
         │       └── ResearchAgent (LLM-powered research)
         │
         ├─── LangGraph Workflow
         │       ├── StateGraph (router → tool/rag/research → END)
         │       ├── Orchestrator (simpler fallback)
         │       ├── MemoryNode
         │       └── SaveMemoryNode
         │
         ├─── LLM Provider Chain (failover)
         │       Gemini → Groq → OpenRouter → OpenAI
         │
         ├─── RAG Pipeline
         │       ├── Embedder (all-MiniLM-L6-v2, 384-dim)
         │       ├── IngestionService (text → vector → pgvector)
         │       ├── Retriever (cosine distance search)
         │       ├── RAGService (retrieve + LLM answer)
         │       └── DocumentIngestion (PDF → chunks → embed → store)
         │
         ├─── Memory Layer
         │       ├── ConversationMemory (in-memory list)
         │       ├── RedisMemory (session-based Redis lists)
         │       └── MemorySummarizer (LLM-based summary)
         │
         ├─── Tools
         │       ├── CalculatorTool (eval-based)
         │       ├── WebSearchTool (placeholder)
         │       └── ToolRegistry
         │
         └─── Data Layer
                 ├── PostgreSQL + pgvector (documents table)
                 ├── SQLAlchemy ORM (psycopg driver)
                 └── Redis (session memory)
```

---

## 3. Current Features

| Feature | Status | Notes |
|---|---|---|
| FastAPI Backend | ✅ Working | Well-structured with versioned API |
| React Frontend | ✅ Working | Chat UI + PDF upload |
| PostgreSQL + pgvector | ✅ Implemented | 384-dimension vector storage |
| Redis Integration | ✅ Implemented | Session-based memory |
| Multi-Agent Router | ✅ Implemented | Keyword-based routing |
| LangGraph Workflow | ✅ Implemented | StateGraph with conditional routing |
| Embedding Generation | ✅ Implemented | sentence-transformers MiniLM |
| Vector Retrieval | ✅ Implemented | Cosine distance search |
| LLM Failover | ✅ Implemented | 4-provider chain |
| Conversation Memory | ✅ Implemented | In-memory + Redis |
| PDF Upload API | ✅ Implemented | Upload → extract → chunk → embed → store |
| Calculator Tool | ✅ Implemented | Uses `eval()` |
| Health Check API | ✅ Implemented | DB + Redis status |

---

## 4. Current Capabilities

### What the system CAN do:
1. Accept a user question via chat UI or API
2. Route the question to the appropriate agent (Tool/RAG/Research)
3. Execute math calculations via CalculatorTool
4. Search vector database for relevant document chunks
5. Generate answers from retrieved context (RAG)
6. Research topics using LLM directly
7. Store/retrieve conversation history in Redis
8. Upload PDF documents, extract text, chunk, embed, and store in pgvector
9. Failover between 4 LLM providers if one fails
10. Health-check database and Redis connectivity

### What the system CANNOT do (yet):
- No authentication/authorization
- No streaming responses
- No multi-document management or metadata
- No MCP protocol support
- No skills framework
- No agent planning/execution loops
- No observability/monitoring
- No evaluation framework

---

## 5. Existing AI Components

### LLM Providers
| Provider | Model | Library | Priority |
|---|---|---|---|
| Gemini | gemini-2.0-flash | google-genai | 1 (primary) |
| Groq | llama-3.3-70b-versatile | groq | 2 |
| OpenRouter | meta-llama/llama-3.3-70b-instruct | openai-compat | 3 |
| OpenAI | gpt-4o-mini | openai | 4 |

### Embedding Model
- **Model:** `all-MiniLM-L6-v2` (sentence-transformers)
- **Dimensions:** 384
- **Use case:** Document + query embedding for pgvector storage/retrieval

### Key ML Libraries Installed
- `langchain 1.3.4`, `langgraph 1.2.4`
- `sentence-transformers 5.5.1`
- `transformers 5.9.0`
- `torch 2.12.0` (CUDA-enabled with NVIDIA drivers)
- `pgvector 0.4.2` (SQLAlchemy integration)

---

## 6. Existing Agent Architecture

### Agent Hierarchy
```
BaseAgent
  ├── ResearchAgent (inherits BaseAgent)
  └── ToolAgent (inherits BaseAgent)

RAGAgent (standalone, uses RAGService)
RouterAgent (standalone, orchestrates all three)
```

### BaseAgent
- Owns an `LLMService` instance and a `ConversationMemory` instance
- `run(prompt)` → adds to memory → calls LLM → stores response → returns

### RouterAgent
- Keyword-based routing (not LLM-based)
- Math keywords → ToolAgent
- RAG keywords → RAGAgent
- Everything else → ResearchAgent

### ToolAgent
- Extends BaseAgent with calculator operations
- Supports "previous result" chain operations
- Hardcoded math operation parsing with regex

### RAGAgent
- Wraps `RAGService`
- ⚠️ **BUG:** Calls `self.rag.ask()` but `RAGService` only has `answer()` method

### ResearchAgent
- Simple LLM prompt wrapper with structured output format

---

## 7. Existing RAG Architecture

### Pipeline Flow
```
PDF File → PDFLoader (pypdf) → Raw Text
       → TextSplitter (500 chars, 50 overlap)
       → Embedder (MiniLM-L6-v2, 384d)
       → pgvector INSERT
       
Query → Embedder → Vector Search (cosine <=>) 
     → Top-K Results → LLM Context Prompt → Answer
```

### Components
| Component | Implementation | Notes |
|---|---|---|
| PDFLoader | `pypdf.PdfReader` | Extracts text page-by-page |
| TextSplitter | Character-based splitting | 500 char chunks, 50 char overlap |
| Embedder | `SentenceTransformer('all-MiniLM-L6-v2')` | 384-dimensional vectors |
| IngestionService | Raw SQL INSERT via SQLAlchemy | Text + vector |
| DocumentIngestion | ORM-based INSERT | Uses SQLAlchemy model |
| Retriever | Cosine distance query | Top-3 by default |
| RAGService | Retrieve + LLM generation | Strict context-only answering |

> [!WARNING]
> There are TWO ingestion paths: `IngestionService` (raw SQL) and `DocumentIngestion` (ORM). This is duplicated logic.

---

## 8. Existing Memory Architecture

### Three Memory Implementations
| Type | Class | Storage | Scope |
|---|---|---|---|
| In-Memory | `ConversationMemory` | Python list | Per-process (volatile) |
| Redis | `RedisMemory` | Redis lists | Per-session (persistent) |
| Summarizer | `MemorySummarizer` | LLM output | On-demand |

### Issues
- `ConversationMemory` is a **global singleton** — all users share the same memory
- `RedisMemory` requires a `session_id` but is not integrated into the main chat flow
- The chat API endpoint uses `RAGService` directly — it does NOT use the memory system at all
- `memory_node` and `save_memory_node` create their OWN `ConversationMemory` instances, disconnected from the agent memory
- Memory is never summarized automatically

---

## 9. Existing APIs

| Method | Endpoint | Handler | Purpose |
|---|---|---|---|
| GET | `/` | root | Returns system status message |
| GET | `/api/v1/health` | health_check | DB + Redis connectivity check |
| POST | `/api/v1/chat` | chat | Send question, get RAG answer |
| POST | `/api/v1/rag` | rag | Direct RAG agent query |
| POST | `/api/v1/research` | research | Research topic via LLM |
| GET | `/api/v1/history` | get_history | Returns conversation memory |
| GET | `/api/v1/history/count` | history_count | Returns message count |
| POST | `/api/v1/upload` | upload_document | Upload PDF for RAG ingestion |

> [!NOTE]
> - `/chat` bypasses the router — it goes directly to `RAGService.answer()`
> - `/rag` uses `RAGAgent.ask()` which has a bug (calls non-existent `ask()` on `RAGService`)
> - No LangGraph workflow is used in any API endpoint
> - No authentication on any endpoint
> - CORS allows all origins (`*`)

---

## 10. Existing Frontend Features

| Feature | Status | Technology |
|---|---|---|
| Chat Interface | ✅ Basic | React + TypeScript |
| PDF Upload UI | ✅ Basic | File input + upload button |
| Message Display | ✅ Basic | User/Assistant bubbles |
| Loading State | ✅ Basic | "AI is thinking..." text |
| Styling | ⚠️ Minimal | Tailwind v4 (classes used directly) |
| Routing | ❌ None | Single page |
| Error Handling | ⚠️ Basic | Console log + generic error message |

### Frontend Tech Stack
- React 19.2.7 + TypeScript 6.0.3
- Vite 8.0.16 (build tool)
- Tailwind CSS v4.3.0 (via `@tailwindcss/vite`)
- Axios 1.17.0 (HTTP client)
- API baseURL: `http://127.0.0.1:8000/api/v1`

---

## 11. Existing Database Components

### PostgreSQL
- **Table:** `documents` (id, content, embedding)
- **Extension:** pgvector with 384-dimensional vectors
- **ORM:** SQLAlchemy 2.0 with mapped columns
- **Driver:** psycopg (async-capable binary driver)
- **Migrations:** Alembic installed but no migration files found

### Redis
- **Use case:** Session-based conversation memory storage
- **Client:** `redis 8.0.0` Python library
- **Data format:** JSON-serialized message lists per session key

---

## 12. Existing Infrastructure

| Component | Status | Notes |
|---|---|---|
| Docker | ❌ Not configured | No Dockerfile or docker-compose |
| CI/CD | ❌ Not configured | No GitHub Actions |
| Environment Config | ✅ Basic | `.env` + pydantic-settings |
| Logging | ✅ Basic | Python logging module |
| CORS | ✅ Permissive | Allow all origins |
| Database Migrations | ⚠️ Partial | Alembic installed, no migrations |
| Virtual Environment | ✅ Present | Python venv at `./venv/` |

### Empty Placeholder Directories
These directories exist but contain no files:
- `agents/` (top-level, distinct from `backend/app/agents/`)
- `docs/`
- `infrastructure/`
- `mcp/`
- `memory/` (top-level, distinct from `backend/app/memory/`)
- `scripts/`
- `tests/` (distinct from `backend/test_*.py`)
- `tools/` (top-level, distinct from `backend/app/tools/`)
- `workflows/`

---

## 13. Existing Test Coverage

### Test Scripts (27 files)
All tests are manual runner scripts (`python test_*.py`), not pytest-compatible tests.

| Test | What It Tests | Uses Real Services? |
|---|---|---|
| test_db.py | PostgreSQL connectivity | ✅ Yes |
| test_redis.py | Redis connectivity | ✅ Yes |
| test_llm.py | LLM generation | ✅ Yes (API calls) |
| test_embedder.py | Embedding generation | ✅ Yes (model load) |
| test_ingestion.py | Vector ingestion | ✅ Yes (DB write) |
| test_retriever.py | Vector search | ✅ Yes (DB read) |
| test_rag.py | RAG pipeline | ✅ Yes (full stack) |
| test_rag_service.py | RAG answering | ✅ Yes (full stack) |
| test_rag_agent.py | RAG agent | ✅ Yes (full stack) |
| test_bulk_ingestion.py | Bulk document ingestion | ✅ Yes (DB writes) |
| test_memory.py | Conversation memory | ❌ In-memory only |
| test_redis_memory.py | Redis memory | ✅ Yes (Redis) |
| test_memory_summary.py | Memory summarization | ✅ Yes (LLM + Redis) |
| test_shared_memory.py | Shared memory across agents | ❌ In-memory only |
| test_sessions.py | Multi-user Redis sessions | ✅ Yes (Redis) |
| test_tool.py | Calculator tool | ❌ Pure logic |
| test_tool_agent.py | Tool agent | ✅ Yes (LLM fallback) |
| test_registry.py | Tool registry | ❌ Pure logic |
| test_router.py | Router agent | ✅ Yes (full stack) |
| test_orchestrator.py | Orchestrator | ✅ Yes (full stack) |
| test_langgraph.py | LangGraph workflow | ✅ Yes (full stack) |
| test_provider_manager.py | Provider manager | ❌ Pure logic |
| test_document_ingestion.py | PDF ingestion | ✅ Yes (DB + file) |
| test_pdf_loader.py | PDF loading | ✅ Yes (file system) |
| test_pdf_retrieval.py | PDF chunk retrieval | ✅ Yes (DB) |
| test_text_splitter.py | Text splitting | ✅ Yes (file system) |

> [!CAUTION]
> - No pytest framework usage
> - No test isolation or mocking
> - No assertions — all tests just print output
> - Tests require live database, Redis, and API keys to run
> - `test_redis_memory.py` instantiates `RedisMemory()` without required `session_id` argument

---

## 14. Technical Debt

### Critical Issues
| # | Issue | Severity | Impact |
|---|---|---|---|
| 1 | **RAGAgent.ask() calls non-existent method** — `RAGService` only has `answer()` | 🔴 Critical | `/api/v1/rag` endpoint will crash |
| 2 | **CalculatorTool uses `eval()`** — arbitrary code execution vulnerability | 🔴 Critical | Security vulnerability |
| 3 | **Global ConversationMemory singleton** — all users share memory | 🔴 Critical | Data leakage between users |
| 4 | **Chat API bypasses router** — goes directly to RAGService | 🟡 Medium | Router/LangGraph is unused in prod |
| 5 | **RedisMemory not integrated in chat flow** — memory is volatile | 🟡 Medium | Conversations lost on restart |
| 6 | **Duplicate ingestion services** — `IngestionService` + `DocumentIngestion` | 🟡 Medium | Inconsistent behavior |
| 7 | **LangGraph workflow not used in any API** | 🟡 Medium | Core feature is orphaned |
| 8 | **No error handling in LLM failover** — exceptions silently swallowed | 🟡 Medium | Silent failures |
| 9 | **memory_node/save_memory_node disconnected** — create own instances | 🟡 Medium | LangGraph memory doesn't work |
| 10 | **requirements.txt incomplete** — missing most installed packages | 🟡 Medium | Deployment will fail |
| 11 | **WebSearchTool is a placeholder** — returns hardcoded string | 🟢 Low | Feature not functional |
| 12 | **Unresolved git merge conflict** noted in PROJECT_GIT_STATUS.txt | 🟢 Low | `.gitignore` conflict |

---

## 15. Missing Components

| Component | Status | Priority |
|---|---|---|
| MCP Server/Client | ❌ Not started | High (core learning goal) |
| Skills Framework | ❌ Not started | High |
| Agent Planner/Executor | ❌ Not started | High |
| Knowledge Graph | ❌ Not started | Medium |
| Workflow Engine | ❌ Not started | Medium |
| Observability/Monitoring | ❌ Not started | Medium |
| Evaluation Framework | ❌ Not started | Medium |
| Human Feedback Loop | ❌ Not started | Medium |
| Multi-Document RAG | ❌ Not started | Medium |
| Hybrid Search | ❌ Not started | Medium |
| Brainstorming Agent | ❌ Not started | Medium |
| Research Workspace | ❌ Not started | Medium |
| Authentication | ❌ Not started | Medium |
| Streaming Responses | ❌ Not started | Medium |
| Docker/Deployment | ❌ Not started | Low |
| CI/CD Pipeline | ❌ Not started | Low |
| Proper Test Suite | ❌ Not started | Low |

---

## 16. Production Readiness Score

| Category | Score | Notes |
|---|---|---|
| Core Functionality | 4/10 | Basic flow works, critical bugs exist |
| Security | 1/10 | eval() vulnerability, no auth, open CORS |
| Reliability | 3/10 | Failover exists but error handling weak |
| Scalability | 2/10 | Global singletons, no async patterns |
| Observability | 1/10 | Basic logging only |
| Testing | 1/10 | No automated tests, no assertions |
| Documentation | 3/10 | Context docs exist, no API docs |
| Deployment | 1/10 | No Docker, no CI/CD |
| **Overall** | **2/10** | Prototype/learning stage |

> [!IMPORTANT]
> This score is expected for a learning project at this stage. The goal is not production readiness — it's learning by building. The score serves as a baseline for measuring progress.

---

## 17. Learning Opportunities

Each planned improvement teaches valuable AI engineering skills:

| Improvement | What You'll Learn |
|---|---|
| Fix RAGAgent bug | API design, method contracts, testing |
| Replace eval() with safe parser | Security-first engineering |
| Integrate LangGraph into chat API | Graph-based agent orchestration |
| Session-based memory in chat | State management in AI systems |
| MCP Server implementation | Model Context Protocol, tool standards |
| Agent Planner/Executor | Autonomous agent loops, ReAct pattern |
| Hybrid Search (BM25 + vector) | Search engineering, relevance tuning |
| Observability (LangSmith/Phoenix) | AI system debugging and monitoring |
| Evaluation framework | LLM output quality measurement |
| Streaming responses | Real-time AI UX patterns |
| Knowledge Graph (Neo4j) | Graph-based reasoning |
| Docker + CI/CD | Production deployment patterns |

---

## 18. Recommended Next Steps

### Immediate (Fix What's Broken)
1. Fix `RAGAgent.ask()` → `RAGAgent.answer()` method name mismatch
2. Replace `eval()` in CalculatorTool with safe expression parser
3. Integrate LangGraph workflow into the `/chat` API endpoint
4. Wire RedisMemory into the chat flow with session management
5. Fix requirements.txt to include all actual dependencies

### Short-Term (Complete Phase 6)
6. Complete the document upload pipeline with proper metadata
7. Add document management API (list, delete, search by metadata)
8. Implement streaming responses (SSE/WebSocket)
9. Add proper error handling and logging throughout

### Medium-Term (Phase 7-8)
10. Implement MCP Server with tool exposure
11. Build Skills Framework for agent capabilities
12. Add Agent Planner/Executor pattern
13. Implement hybrid search (BM25 + vector)
14. Add evaluation and observability

### Long-Term (Phase 9-10)
15. Knowledge Graph integration
16. Multi-agent collaboration protocols
17. Human-in-the-loop feedback
18. Production deployment pipeline
