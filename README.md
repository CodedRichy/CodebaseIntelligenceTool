<div align="center">

# CodeSense AI

**Talk to your codebase.**

AI-powered tool that parses source code into a Neo4j knowledge graph and lets you query your codebase in natural language using Grok/xAI.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-3776ab?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/fastapi-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Neo4j](https://img.shields.io/badge/neo4j-4581C3?style=flat-square&logo=neo4j&logoColor=white)](https://neo4j.com)

</div>

---

## What It Does

Point CodeSense at any GitHub repo. It clones, parses the AST with Tree-sitter, maps symbols into a Neo4j graph, then lets you ask natural language questions about the code.

```
"Which files depend on authentication logic?"
"What happens if I change this function?"
"Show me all imports in app.py"
```

## How It Works

1. **Ingest** -- Clones repo to temp directory
2. **Parse** -- Tree-sitter generates ASTs, extracts symbols (classes, functions, imports)
3. **Graph** -- Maps symbols into Neo4j nodes with relationships (`IMPORTS`, `CALLS`, `DEFINES`)
4. **Reason** -- Grok analyzes graph structure for context-aware answers

## Features

- **Multi-Language Parsing** -- Python, JavaScript, TypeScript via Tree-sitter
- **Knowledge Graph** -- Tracks file imports, cross-file function calls, class hierarchies
- **Natural Language Queries** -- Ask questions, get graph-backed answers
- **VS Code Extension** -- Query your codebase directly from the editor
- **Web UI** -- Glassmorphic chat interface with real-time stats

## Quick Start

### Prerequisites

- Python 3.10+
- [Neo4j](https://neo4j.com/download/) running on `bolt://localhost:7687`
- xAI API key (for Grok LLM)

### Install

```bash
git clone https://github.com/CodedRichy/CodebaseIntelligenceTool.git
cd CodebaseIntelligenceTool/backend
pip install -r requirements.txt
```

### Configure

```bash
# backend/.env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
GROK_API_KEY=your_xai_key
```

### Run

```bash
cd backend
python -m uvicorn app:app --reload
```

Open `frontend/index.html` in your browser (or `python -m http.server 3000`).

## Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | FastAPI, Uvicorn |
| **AI/LLM** | Grok (xAI API), LangChain |
| **Graph DB** | Neo4j |
| **Parsing** | Tree-sitter (Python, JS, TS) |
| **Frontend** | Vanilla HTML/CSS/JS |
| **VS Code** | TypeScript extension |

## Project Structure

```
backend/            FastAPI app, parsers, graph builder, AI engine
database/           Neo4j Cypher schema
frontend/           Single-page web interface
vscode-extension/   VS Code extension (TypeScript)
```

---

<div align="center">

Built by [Rishi Praseeth Krishnan](https://rishipraseeth.in)

</div>
