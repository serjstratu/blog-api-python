from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.modules.users.router import router as users_router
from app.modules.auth.router import router as auth_router


app = FastAPI(
    title="Blog API",
    description="Blog API built with FastAPI",
    version="1.0.0"
)

app.include_router(
    users_router,
    prefix="/api"
)

app.include_router(
    auth_router,
    prefix="/api"
)


@app.get("/health")
def health_check():
    return {"status": "ok"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)