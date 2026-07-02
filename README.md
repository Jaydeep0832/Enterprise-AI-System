<div align="center">

# 🧠 Enterprise AI System

### Production-Grade Multi-Agent RAG Platform with Knowledge Graphs, Memory, and Observability

[![Python](https://img.shields.io/badge/Python-3.14-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.136-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.2-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white)](https://langchain-ai.github.io/langgraph/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16_pgvector-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-8.0-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

<br/>

**Not just another chatbot.** This is a full-stack, enterprise-ready AI platform that orchestrates specialized agents, builds knowledge graphs from your documents, remembers conversations across sessions, and gives you production observability — all with a single `docker-compose up`.

[Architecture](#-architecture) · [Key Features](#-what-makes-this-different) · [Tech Stack](#-tech-stack) · [Quick Start](#-quick-start) · [API Reference](#-api-endpoints) · [Deployment](#-deployment)

</div>

---

## 🎯 The Problem This Solves

Most RAG applications are **fragile, single-pipeline systems** that:

- ❌ Treat every query the same — a math question and a research question go through the same pipeline
- ❌ Lose context after every conversation — no memory, no continuity
- ❌ Do flat vector search only — missing relationships between entities in your documents
- ❌ Have zero observability — you can't tell why a response was bad, or what it cost
- ❌ Can't self-improve — no feedback loops, no prompt optimization

**Enterprise AI System solves all of these.**

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        React Frontend (Vite + Tailwind)            │
│  ┌──────────┐  ┌────────────┐  ┌───────────┐  ┌────────────────┐  │
│  │ Chat UI  │  │ Knowledge  │  │ Dashboard │  │  Evaluation    │  │
│  │ + Upload │  │ Graph Viz  │  │ + Metrics │  │  Console       │  │
│  └──────────┘  └────────────┘  └───────────┘  └────────────────┘  │
└───────────────────────────┬─────────────────────────────────────────┘
                            │  REST API
┌───────────────────────────▼─────────────────────────────────────────┐
│                     FastAPI Backend (Python)                        │
│                                                                     │
│  ┌─────────────────── LangGraph Orchestrator ──────────────────┐   │
│  │                                                              │   │
│  │   Load Memory ──▶ Router ──▶ ┌──────────────┐ ──▶ Save     │   │
│  │                               │ RAG Agent    │     Memory   │   │
│  │   (Redis context              │ Research     │              │   │
│  │    injection)                 │ Tool Agent   │              │   │
│  │                               │ Supervisor   │              │   │
│  │                               │ Brainstorm   │              │   │
│  │                               │ GraphRAG     │              │   │
│  │                               │ General      │              │   │
│  │                               └──────────────┘              │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │ Knowledge    │  │ Evaluation   │  │ Observability            │  │
│  │ Graph Store  │  │ Engine       │  │ (Tracing + Cost + Perf)  │  │
│  │ (NetworkX +  │  │ (RAG + Agent │  │                          │  │
│  │  PostgreSQL) │  │  Evaluator)  │  │ Token counting, p50/95/  │  │
│  └──────────────┘  └──────────────┘  │ 99 latency, $/provider  │  │
│                                       └──────────────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │ MCP Client   │  │ Hybrid RAG   │  │ Prompt Optimizer         │  │
│  │ (Tool Proto  │  │ (Vector +    │  │ (Feedback-driven         │  │
│  │  col)        │  │  Keyword RRF)│  │  self-improvement)       │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘  │
└─────────────────────┬──────────────────┬────────────────────────────┘
                      │                  │
         ┌────────────▼──┐        ┌──────▼──────┐
         │  PostgreSQL   │        │    Redis    │
         │  + pgvector   │        │  (Memory +  │
         │  (Documents,  │        │   Metrics + │
         │   KG, Users)  │        │   Sessions) │
         └───────────────┘        └─────────────┘
```

---

## ✨ What Makes This Different

### 1. 🤖 Multi-Agent Orchestration (Not Just a Single Pipeline)

Most RAG apps have one pipeline. This system has **7 specialized agents** orchestrated via a LangGraph state machine:

| Agent | Purpose | When It Activates |
|-------|---------|-------------------|
| **RAG Agent** | Document Q&A with source citations | Questions about uploaded documents |
| **Research Agent** | Live web search + synthesis | Current events, external knowledge |
| **Tool Agent** | Calculator, web search tools | Math, calculations, tool-use queries |
| **Supervisor Agent** | Multi-step task decomposition | Complex tasks requiring planning |
| **Brainstorm Agent** | Idea generation with self-critique | Creative and strategy questions |
| **GraphRAG Agent** | Knowledge graph + vector hybrid | Relationship-heavy questions |
| **General Agent** | Fast direct LLM response | Simple, conversational queries |

The **Router Agent** uses LLM-powered intent classification to dispatch each query to the right specialist — no one-size-fits-all.

### 2. 🕸️ Knowledge Graphs (Beyond Flat Vector Search)

Standard RAG retrieves text chunks. **GraphRAG retrieves relationships.**

- Automatically extracts **entities and relationships** from uploaded documents using LLM
- Stores them in a **dual-layer graph** (NetworkX in-memory + PostgreSQL persistent)
- **Interactive force-directed visualization** in the frontend — explore your knowledge visually
- Combines graph context with vector retrieval for richer, more structured answers
- Supports entity search, neighbor traversal, and batch ingestion with deduplication

### 3. 🧠 Persistent Memory (Conversations Don't Disappear)

Three layers of memory, inspired by human cognition:

| Layer | What It Stores | How It Works |
|-------|---------------|--------------|
| **Conversational** | Current chat history | Redis lists per session |
| **Episodic** | Past task completions | Stored results for cross-session recall |
| **Summarized** | Compressed context | LLM-generated summaries when context grows |

The LangGraph workflow **automatically loads memory** before routing and **saves memory** after every response — zero manual context management.

### 4. 🔍 Hybrid Retrieval with RRF (Not Just Cosine Similarity)

The retriever combines **two search strategies** using Reciprocal Rank Fusion:

```sql
-- Semantic search (pgvector cosine distance)
embedding <=> CAST(:embedding AS vector)

-- Keyword search (PostgreSQL full-text tsvector)
search_vector @@ websearch_to_tsquery('english', :query)

-- Combined via Reciprocal Rank Fusion
COALESCE(1.0 / (60 + semantic.rank), 0.0) +
COALESCE(1.0 / (60 + keyword.rank), 0.0) AS rrf_score
```

This ensures you get results that are **both semantically similar AND keyword-relevant**, outperforming either method alone.

### 5. 📊 Built-in RAG Evaluation (Know If Your System Is Actually Working)

Five automated quality metrics powered by LLM-as-judge:

| Metric | What It Measures |
|--------|-----------------|
| **Faithfulness** | Does the answer only use info from the context? |
| **Answer Relevancy** | Is the answer relevant to the question? |
| **Context Precision** | Are the retrieved chunks actually relevant? (embedding similarity) |
| **Context Recall** | How much of the expected answer is covered? |
| **Hallucination Detection** | Does the answer contain fabricated facts? |

Run evaluations from the frontend, track scores over time, and identify weak points.

### 6. 📈 Production Observability (Not a Black Box)

Every LLM call is traced and recorded with:

- **Token counting** (input/output per call)
- **Cost estimation** per provider (OpenAI, Gemini, Groq, OpenRouter pricing)
- **Latency percentiles** (p50, p95, p99)
- **Per-agent execution metrics** (calls, success rate, avg latency)
- **Error rate tracking** (1h/24h windows with recent error logs)
- **Daily/hourly cost breakdown** by provider

All metrics are stored in Redis and exposed via dedicated API endpoints + a dashboard UI.

### 7. 🔄 Self-Improving Prompts (Feedback Loop)

The system doesn't just collect user feedback — it **acts on it**:

1. Users give thumbs up/down on responses
2. The **Prompt Optimizer** analyzes negative feedback patterns using LLM meta-analysis
3. It identifies failure categories (e.g., "RAG answers are too verbose", "Router misclassifies math queries")
4. Generates **specific, actionable prompt improvements** per agent

### 8. 🔌 MCP Integration (Enterprise Tool Connectivity)

Built-in **Model Context Protocol** client for secure tool integration:

- Connects to any MCP-compatible server
- Dynamic tool discovery (`list_tools`)
- Sync wrappers for agent consumption
- Extensible — add Jira, Slack, databases, or any enterprise tool

---

## 🛠 Tech Stack

### Backend
| Technology | Purpose |
|-----------|---------|
| **FastAPI** | High-performance async API framework |
| **LangGraph** | Multi-agent state machine orchestration |
| **LangChain** | LLM abstractions and chain composition |
| **PostgreSQL 16 + pgvector** | Document storage with vector search |
| **Redis 7** | Session memory, metrics, caching |
| **NetworkX** | In-memory knowledge graph operations |
| **Sentence Transformers** | Local embedding generation |
| **Alembic** | Database migrations |
| **MCP SDK** | Model Context Protocol client |

### Frontend
| Technology | Purpose |
|-----------|---------|
| **React 19** | UI framework |
| **TypeScript** | Type safety |
| **Vite 8** | Build tooling |
| **Tailwind CSS 4** | Utility-first styling |
| **Framer Motion** | Animations and transitions |
| **Recharts** | Dashboard data visualization |
| **Lucide React** | Icon system |
| **React Router 7** | Client-side routing |

### LLM Providers (Multi-Provider Support)
| Provider | Models |
|----------|--------|
| **Google Gemini** | gemini-2.0-flash, gemini-pro |
| **OpenAI** | gpt-4o, gpt-4o-mini |
| **Groq** | llama, mixtral (ultra-fast inference) |
| **OpenRouter** | Any model via unified API |

### Infrastructure
| Technology | Purpose |
|-----------|---------|
| **Docker Compose** | One-command local deployment |
| **Render** | One-click cloud deployment (render.yaml included) |
| **Alembic** | Schema migrations |

---

## 🚀 Quick Start

### Prerequisites

- **Docker** & **Docker Compose** (recommended)
- **Python 3.12+** (if running without Docker)
- **Node.js 20+** (if running without Docker)
- At least one LLM API key (Gemini, OpenAI, Groq, or OpenRouter)

### Option 1: Docker (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/Jaydeep0832/Enterprise-AI-System.git
cd Enterprise-AI-System

# 2. Set up environment variables
cp .env.example backend/.env
# Edit backend/.env and add your API key(s):
#   GEMINI_API_KEY=your_key_here
#   OPENAI_API_KEY=your_key_here   (optional)
#   GROQ_API_KEY=your_key_here     (optional)

# 3. Launch everything
docker-compose up -d

# 4. Open the app
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Option 2: Manual Setup

```bash
# 1. Clone and navigate
git clone https://github.com/Jaydeep0832/Enterprise-AI-System.git
cd Enterprise-AI-System

# 2. Start databases (requires Docker for this step)
docker-compose up -d postgres redis

# 3. Backend setup
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp ../.env.example .env
# Edit .env with your API keys and database credentials

# Run database migrations
alembic upgrade head

# Start the backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 4. Frontend setup (new terminal)
cd frontend
npm install
npm run dev
```

### Option 3: One-Click Cloud Deploy (Render)

This project includes a [`render.yaml`](render.yaml) blueprint for instant deployment:

1. Fork this repository
2. Go to [Render Dashboard](https://dashboard.render.com) → **New** → **Blueprint**
3. Connect your forked repo
4. Render will automatically provision PostgreSQL, Redis, Backend, and Frontend
5. Add your API keys as environment variables in the Render dashboard

---

## 📁 Project Structure

```
Enterprise-AI-System/
├── backend/
│   ├── app/
│   │   ├── agents/                 # Specialized AI agents
│   │   │   ├── base_agent.py       #   Base class for all agents
│   │   │   ├── router_agent.py     #   Intent classification & routing
│   │   │   ├── rag_agent.py        #   Document Q&A with citations
│   │   │   ├── research_agent.py   #   Web search + synthesis
│   │   │   ├── tool_agent.py       #   Calculator & tool execution
│   │   │   ├── supervisor_agent.py #   Multi-step task orchestrator
│   │   │   ├── brainstorm_agent.py #   Idea generation + self-critique
│   │   │   └── planner_agent.py    #   Task decomposition
│   │   ├── graph/                  # LangGraph workflow
│   │   │   ├── langgraph_workflow.py  # State machine definition
│   │   │   ├── memory_node.py      #   Memory loading node
│   │   │   └── save_memory_node.py #   Memory persistence node
│   │   ├── knowledge_graph/        # Knowledge graph engine
│   │   │   ├── graph_store.py      #   NetworkX + PostgreSQL dual store
│   │   │   ├── entity_extractor.py #   LLM-based entity extraction
│   │   │   └── graph_rag.py        #   Graph-augmented retrieval
│   │   ├── rag/                    # Document processing pipeline
│   │   │   ├── document_ingestion.py  # Upload -> chunk -> embed -> store
│   │   │   ├── embedder.py         #   Sentence transformer embeddings
│   │   │   ├── retriever.py        #   Hybrid search (RRF)
│   │   │   ├── text_splitter.py    #   Intelligent chunking
│   │   │   ├── pdf_loader.py       #   PDF parsing
│   │   │   └── rag_service.py      #   End-to-end RAG pipeline
│   │   ├── memory/                 # Multi-layer memory system
│   │   │   ├── redis_memory.py     #   Conversational + episodic memory
│   │   │   ├── conversation_memory.py  # Session management
│   │   │   ├── long_term_memory.py #   Persistent knowledge
│   │   │   └── memory_summarizer.py#   Context compression
│   │   ├── evaluation/             # Quality assurance
│   │   │   ├── rag_evaluator.py    #   5-metric RAG evaluation
│   │   │   ├── agent_evaluator.py  #   Agent performance tracking
│   │   │   └── prompt_optimizer.py #   Feedback-driven improvement
│   │   ├── services/               # Core services
│   │   │   ├── llm_service.py      #   Multi-provider LLM gateway
│   │   │   ├── provider_manager.py #   Provider registry
│   │   │   └── providers.py        #   Provider definitions
│   │   ├── mcp/                    # Model Context Protocol
│   │   │   └── mcp_client.py       #   Enterprise tool integration
│   │   ├── skills/                 # Skill system
│   │   │   ├── base_skill.py       #   Extensible skill framework
│   │   │   ├── skill_registry.py   #   Dynamic skill loading
│   │   │   ├── mcp_skill.py        #   MCP-backed skills
│   │   │   └── memory_skill.py     #   Memory-backed skills
│   │   ├── tools/                  # Tool implementations
│   │   │   ├── calculator_tool.py  #   Math operations
│   │   │   ├── web_search_tool.py  #   DuckDuckGo integration
│   │   │   └── registry.py         #   Tool registry
│   │   ├── core/                   # Infrastructure
│   │   │   ├── config.py           #   Settings (pydantic-settings)
│   │   │   ├── tracing.py          #   Full observability pipeline
│   │   │   ├── auth.py             #   JWT authentication
│   │   │   ├── middleware.py       #   Request timing
│   │   │   └── logger.py           #   Structured logging
│   │   ├── api/v1/                 # REST API endpoints
│   │   ├── models/                 # SQLAlchemy models
│   │   ├── schemas/                # Pydantic schemas
│   │   └── main.py                 # Application entry point
│   ├── alembic/                    # Database migrations
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatWindow.tsx      # Chat interface with source cards
│   │   │   ├── ChatInput.tsx       # Smart input with mode switching
│   │   │   ├── Sidebar.tsx         # Session management sidebar
│   │   │   ├── KnowledgeGraphPage.tsx  # Interactive graph explorer
│   │   │   ├── DashboardPage.tsx   # Metrics & observability
│   │   │   ├── EvaluationPage.tsx  # RAG quality evaluation
│   │   │   └── AuthPage.tsx        # Authentication
│   │   ├── services/api.ts         # API client
│   │   ├── App.tsx                 # Root routing
│   │   └── index.css               # Design system
│   ├── Dockerfile
│   └── package.json
├── tests/                          # Comprehensive test suite
├── docker-compose.yml              # One-command deployment
├── render.yaml                     # Render cloud blueprint
└── .env.example                    # Environment template
```

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/chat` | Send a message (auto-routed to best agent) |
| `POST` | `/api/v1/upload` | Upload documents (PDF, TXT, MD, DOCX) |
| `GET` | `/api/v1/history/{session_id}` | Get conversation history |
| `GET` | `/api/v1/health` | Health check + dependency status |
| `POST` | `/api/v1/auth/register` | User registration |
| `POST` | `/api/v1/auth/login` | JWT authentication |
| `GET` | `/api/v1/metrics` | LLM call metrics & cost tracking |
| `POST` | `/api/v1/feedback` | Submit response feedback |
| `POST` | `/api/v1/evaluation/run` | Run RAG quality evaluation |
| `GET` | `/api/v1/knowledge-graph` | Get full knowledge graph |
| `POST` | `/api/v1/knowledge-graph/build` | Build KG from documents |
| `GET` | `/api/v1/rag/search?q=...` | Direct hybrid search |

Full interactive docs available at **`/docs`** (Swagger UI) once the server is running.

---

## 📊 Observability Dashboard

The built-in dashboard provides real-time visibility into:

- **Total LLM calls**, success/error rates
- **Cost tracking** by provider (daily, hourly, per-session)
- **Latency percentiles** (p50, p95, p99)
- **Per-agent metrics** (which agents are used most, their success rates)
- **Error logs** with timestamps and provider context
- **Token usage** (input/output)

---

## 🧪 Running Tests

```bash
cd backend
pytest -v                        # Run all tests
pytest tests/test_chat.py        # Test chat functionality
pytest tests/test_upload.py      # Test document upload
pytest tests/test_memory.py      # Test memory system
pytest tests/test_tool_agent.py  # Test tool execution
```

---

## 🔧 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | At least one | Google Gemini API key |
| `OPENAI_API_KEY` | At least one | OpenAI API key |
| `GROQ_API_KEY` | At least one | Groq API key (fast inference) |
| `OPENROUTER_API_KEY` | At least one | OpenRouter unified API key |
| `POSTGRES_HOST` | Yes | PostgreSQL host (default: localhost) |
| `POSTGRES_PORT` | No | PostgreSQL port (default: 5432) |
| `POSTGRES_DB` | No | Database name (default: enterprise_ai) |
| `POSTGRES_USER` | No | Database user (default: postgres) |
| `POSTGRES_PASSWORD` | Yes | Database password |
| `REDIS_HOST` | No | Redis host (default: localhost) |
| `REDIS_PORT` | No | Redis port (default: 6379) |

---

## 🗺️ Roadmap

- [ ] Streaming responses (SSE)
- [ ] Multi-modal document support (images, audio)
- [ ] Agent collaboration (agents consulting each other)
- [ ] Custom fine-tuning pipeline
- [ ] Kubernetes deployment manifests
- [ ] Role-based access control (RBAC)
- [ ] Webhook integrations (Slack, Teams)

---

## 🤝 Contributing

Contributions are welcome! Here's how:

1. **Fork** the repository
2. **Create** your feature branch (`git checkout -b feat/amazing-feature`)
3. **Commit** your changes (`git commit -m 'feat: add amazing feature'`)
4. **Push** to the branch (`git push origin feat/amazing-feature`)
5. **Open** a Pull Request

Please follow [Conventional Commits](https://www.conventionalcommits.org/) for commit messages.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Jaydeep Parmar**

- GitHub: [@Jaydeep0832](https://github.com/Jaydeep0832)

---

<div align="center">

**If this project helped you or gave you ideas, consider giving it a ⭐**

Built with persistence, curiosity, and way too much coffee ☕

</div>
