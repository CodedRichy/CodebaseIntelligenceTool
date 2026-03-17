# CodeSense AI 🧠

**CodeSense AI** is a powerful codebase intelligence tool that transforms your static source code into a dynamic, queryable knowledge graph. By combining **Tree-sitter** for advanced parsing, **Neo4j** for relationship tracking, and **Grok (xAI)** for natural language understanding, CodeSense allows developers to "talk" to their codebase.

---

## ✨ Features

- 📂 **Multi-Language Parsing**: Deep structural analysis of Python, JavaScript, and TypeScript using Tree-sitter.
- 🕸️ **Knowledge Graph**: Tracks complex relationships including file imports and cross-file function calls.
- 💬 **Natural Language Queries**: Ask questions like *"Which files depend on authentication logic?"* or *"What happens if I change this function?"*
- 🎨 **Premium UI**: Modern, glassmorphic chat interface with real-time stats and visual feedback.
- 🚀 **Fast Ingestion**: Rapidly clone and index local or remote repositories.

---

## 🛠️ Tech Stack

- **Frontend**: Vanilla HTML5, CSS3 (Glassmorphism), JavaScript (ES6+), Lucide Icons.
- **Backend**: FastAPI (Python 3.10+), Uvicorn.
- **AI/LLM**: Grok-beta (via xAI API), LangChain.
- **Database**: Neo4j (Graph Database).
- **Parsers**: Tree-sitter.

---

## 🚀 Getting Started

### 1. Prerequisites
- **Neo4j**: Ensure Neo4j is installed and running (default: `bolt://localhost:7687`).
- **Python 3.10+**
- **xAI API Key**: Required for the Grok LLM.

### 2. Installation

```bash
# Clone the project
git clone https://github.com/CodedRichy/CodebaseIntelligenceTool.git
cd CodebaseIntelligenceTool

# Install dependencies
cd backend
pip install -r requirements.txt
```

### 3. Configuration
Update the `backend/.env` file with your credentials:
```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
GROK_API_KEY=your_xai_key
```

### 4. Running the Tool

**Start the Backend:**
```bash
cd backend
python -m uvicorn app:app --reload
```

**Open the Frontend:**
Simply open `frontend/index.html` in your browser. (Or serve it via `python -m http.server 3000`).

---

## 📖 Usage

1. **Ingest**: Paste a GitHub URL (e.g., `https://github.com/fastapi/fastapi`) into the sidebar and click **Ingest**.
2. **Analyze**: Once the progress bar finishes, you'll see file and function counts.
3. **Query**: Ask any question in the chat. Examples:
   - *"What are the main entry points of this app?"*
   - *"Show me all imports in app.py"*
   - *"Which functions call the database directly?"*

---

## 🏗️ Architecture

CodeSense AI works in four stages:
1. **Ingestion**: Clones the repo to a temp directory.
2. **Parsing**: Uses Tree-sitter to generate ASTs and extract symbols (Classes, Functions, Imports).
3. **Graphing**: Maps those symbols into Neo4j nodes and creates relationships (`IMPORTS`, `CALLS`, `DEFINES`).
4. **Reasoning**: Grok analyzes the graph structure to provide context-aware answers.

---

*Built with ❤️ for developers who hate reading legacy code.*