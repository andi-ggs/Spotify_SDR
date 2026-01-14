from fastapi import FastAPI
from .routers import users, tracks, events, recommendations, auth
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Spotify SR Backend (SQLite + Recombee)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(tracks.router)
app.include_router(events.router)
app.include_router(recommendations.router)
app.include_router(auth.router)
