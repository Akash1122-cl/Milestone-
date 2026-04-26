import sys
import traceback

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    from typing import Optional
    import os

    from core.enhanced_retriever import retrieve_context
    from core.generator import generate_answer, is_advisory_query, REFUSAL_PROMPT
    from routers.metrics import router as metrics_router
except Exception as e:
    print(f"CRITICAL ERROR DURING IMPORT: {e}", file=sys.stderr)
    traceback.print_exc()
    raise

app = FastAPI(title="Mutual Fund FAQ API", description="Facts-only RAG backend")

# Allow Next.js frontend to communicate
# NOTE: allow_credentials=True is INCOMPATIBLE with allow_origins=["*"] — browsers reject it.
# Use an explicit origins list instead.
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://web-gamma-weld-29.vercel.app",   # Production Vercel URL
    "https://milestone-1-o899.onrender.com",   # Backend self-reference
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",  # Allow all Vercel preview deployments
    allow_credentials=False,   # Must be False when using wildcard-like origins
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

class QueryRequest(BaseModel):
    thread_id: str
    query: str
    scheme_name: Optional[str] = None

class QueryResponse(BaseModel):
    answer: str
    citation: Optional[str]
    last_updated: Optional[str]
    is_advisory: bool

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Include metrics router
app.include_router(metrics_router)

@app.post("/api/chat/query", response_model=QueryResponse)
async def chat_query(req: QueryRequest):
    # 1. Refusal Engine (Guardrail Check)
    if is_advisory_query(req.query):
        return QueryResponse(
            answer=REFUSAL_PROMPT.strip(),
            citation=None,
            last_updated=None,
            is_advisory=True
        )

    # 2. Retriever Engine (Querying ChromaDB)
    context, citation, updated_date = retrieve_context(req.query, req.scheme_name, top_k=3)

    # 3. Generator Engine (OpenAI synthesized factual answer)
    answer = generate_answer(req.query, context)

    return QueryResponse(
        answer=answer,
        citation=citation if citation else None,
        last_updated=updated_date if updated_date else None,
        is_advisory=False
    )

# Run instructions:
# cd "apps/api"
# uvicorn main:app --reload
