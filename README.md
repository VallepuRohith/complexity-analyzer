# Complexity Analyzer

A Python time and space complexity analyzer with a FastAPI backend and a modern React frontend.

## Project Structure

- `server.py`: FastAPI server providing API endpoints (`/api/analyze`, `/api/examples`, `/api/health`) and serving frontend static files in production.
- `complexity_analyzer/`: Core AST-based static code analysis logic for time and auxiliary space complexity.
- `frontend/`: React + Vite interactive UI for code editing, real-time complexity analysis, and visualization.
- `requirements.txt`: Python backend dependencies for deployment and local execution.
- `Dockerfile`: Multi-stage build producing an all-in-one production container.
- `render.yaml`: Render Blueprint for automated deployment.
- `Procfile`: Web process definition for PaaS deployment (Render, Heroku, Railway).

## Local Development

### 1. Backend
```bash
pip install -r requirements.txt
python server.py
# Running on http://127.0.0.1:8000
```

### 2. Frontend
```bash
cd frontend
npm install
npm run dev
# Running on http://localhost:5173
```

## Deployment on Render

### Option A: 1-Click All-in-One Deployment (Recommended)
1. In your Render Dashboard, click **New +** -> **Blueprint**.
2. Connect this repository (`VallepuRohith/complexity-analyzer`).
3. Render will detect `render.yaml` and `Dockerfile`, automatically building both the React frontend and FastAPI backend into a single service.
4. Your application will be live at `https://complexity-analyzer.onrender.com`.

### Option B: Manual Web Service
- **Environment**: Docker
- **Branch**: `main`
- **Health Check Path**: `/api/health`
