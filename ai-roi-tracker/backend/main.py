from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import create_db
from routers import events, metrics, integrations

app = FastAPI(title="AI ROI Tracker", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    create_db()


app.include_router(events.router)
app.include_router(metrics.router)
app.include_router(integrations.router)


@app.get("/health")
def health():
    return {"status": "ok"}
