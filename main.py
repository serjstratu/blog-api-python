from fastapi import FastAPI

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