# Silent-Roar
Silent Roar is an AI-powered wildlife intelligence platform built to dismantle transnational poaching networks before they strike. Designed as a software-only solution, it transforms fragmented, messy data—seizure records, satellite imagery, animal movement patterns, and online trafficking chatter—into a unified, living network graph.

## Run the Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API: http://localhost:8000  
Swagger docs: http://localhost:8000/docs

## Run the Frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:5173
