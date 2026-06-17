# AMKGC / Node-LLM System — portfolio notes

See [README.md](README.md) and the many design docs (`*_README.md`,
`*_SUMMARY.md`, `*_PLAN.md`) for full detail. This is the short version.

## What it is

The most ambitious project in the set: a **node-based LLM orchestration
platform**. You build a graph of LLM "nodes" on a canvas — each node holds
structured context and talks to a local LLM (Ollama, with Qwen/OpenAI fallbacks)
— and the system manages context, detects conflicts between nodes, tracks
hallucination/reliability, versions changes, and runs work across distributed
agents. FastAPI backend, React/TypeScript canvas frontend, Neo4j graph store +
Postgres + Redis.

## What I built

Backend (FastAPI, `backend/`):
- **LLM abstraction** — `llm_abstraction.py`, providers for Ollama (`llm_ollama`,
  `ollama_provider`, `ollama_embedder`, `ollama_warmup`, `ollama_supervisor`) and
  Qwen (`llm_qwen`).
- **Graph + storage** — Neo4j service + `scripts/migrate_to_neo4j.py`, Redis
  service, SQLAlchemy node models.
- **Services** — conflict resolution, clarification, continuation (token-limit
  handling), versioning, analytics, export/import, auth/security, health, vector
  search/embeddings.
- **Distributed execution** — `distributed/` agent / coordinator / router / merge
  + a `distributed_cli.py`.
- **API layer** — REST endpoints + WebSocket realtime sync, Prometheus metrics,
  Dockerfiles and `docker-compose` (incl. a Neo4j compose).
- Tests for conflict + LLM services; throughput benchmark script.

Frontend (`frontend-minimal/`, React + TypeScript + Vite):
- A **tldraw/reactflow canvas** (`components/canvas/`) for building the node
  graph, node-specific chat panels, clarification + hallucination markers,
  continuation badges, a reliability/hallucination-heatmap dashboard, diff +
  merge-preview viewers, and a commit-history view.

## Cleanup done in this pass (2026)

This was the big one. The single "Initial Commit" had tracked everything:

- Removed a committed **virtualenv** (`as/`, thousands of site-packages files).
- Removed a committed **`node_modules/`** under `frontend-minimal/`.
- Removed `__pycache__/` and `.pyc` files.
- Removed two tracked env files (`.env`, `b.env`) — both held only placeholder/dev
  values (`NEO4J_PASSWORD=password`, `OPENAI_API_KEY=your-openai-key`,
  `QWEN_API_KEY=YOUR_QWEN_API_KEY`), so no real secrets leaked.
- Added a `.gitignore` (venv/node_modules/env/db) and a `.env.example` documenting
  the required config.

**Result: 33,757 tracked files → 297.** The repo is now actually browsable.

## Honest status

Single-commit dump of a large, heavily AI-assisted system with ~25 design/summary
markdown docs. The breadth is real (a lot of services and frontend components
exist), but with no commit history it's hard to gauge how much is fully wired vs
scaffolded — treat it as an ambitious prototype. Note the README describes the
frontend as D3/Material-UI/Redux while the actual `frontend-minimal` is
Vite/tldraw/zustand, so the docs and code drifted apart in places.
