from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.modules.books.controller import router as books_router
from app.modules.chat.controller import router as chat_router

app = FastAPI(
    title="Smart Library API",
    description="API for managing books, uploads, processing status, and semantic chunks.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(
    "/health",
    summary="Health check",
    description="Returns the API health status.",
)
def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(books_router)
app.include_router(chat_router)
