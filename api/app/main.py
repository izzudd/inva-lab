from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

from . import repositories
from .db import SessionLocal, query_counter

app = FastAPI(title="Inva Lab - N+1 Query")


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.get("/api/posts")
def list_posts(limit: int = Query(20, ge=1, le=200)):
    query_counter.reset()

    with SessionLocal() as session:
        data = repositories.list_posts(session, limit)

    return JSONResponse(
        content=data,
        headers={"X-Db-Query-Count": str(query_counter.value)},
    )
