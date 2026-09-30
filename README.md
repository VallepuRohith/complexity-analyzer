# Complexity Analyzer

A Python time and space complexity analyzer with a FastAPI backend and a modern React frontend.

## Project Structure

- `server.py`: FastAPI server providing API endpoints (`/api/analyze`, `/api/examples`, `/api/health`).
- `complexity_analyzer/`: Core AST-based static code analysis logic for time and auxiliary space complexity.
- `frontend/`: React + Vite interactive UI for code editing, real-time complexity analysis, and visualization.
- `requirements.txt`: Python backend dependencies for deployment and local execution.
- `Procfile`: Web process definition for PaaS deployment (Render, Heroku, Railway).

## Backend Setup & Run

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Server
```bash
# Direct Python run
python server.py

# Or via Uvicorn CLI
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

## Deployment Commands

- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn server:app --host 0.0.0.0 --port $PORT`
