
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests, json, os

with open("config/config.json", "r") as f:
    cfg = json.load(f)

EMBED_URL = cfg["embedding_service_url"].rstrip("/") + "/embed"
VECTOR_QUERY = cfg["vector_db_url"].rstrip("/") + "/query"
LLM_URL = cfg["llm_service_url"].rstrip("/") + "/generate"
N_RESULTS = cfg.get("n_results", 3)
PROMPT_TEMPLATE = cfg.get("prompt_template")

app = FastAPI(title="RAG Orchestrator")

class AskReq(BaseModel):
    question: str

@app.post("/ask")
def ask(req: AskReq):
    # 1) embed question
    r = requests.post(EMBED_URL, json={"texts": [req.question]}, timeout=30)
    if r.status_code != 200:
        raise HTTPException(status_code=502, detail="Embedding service error")
    qvec = r.json()["embeddings"][0]
    # 2) query vector DB
    r2 = requests.post(VECTOR_QUERY, json={"vector": qvec, "top_k": N_RESULTS}, timeout=30)
    if r2.status_code != 200:
        raise HTTPException(status_code=502, detail="Vector DB error")
    results = r2.json().get("results", [])
    # 3) build context
    contexts = []
    for res in results:
        md = res.get("metadata", {}) or {}
        source = md.get("source", "unknown")
        text = md.get("text", "")
        # truncate long texts to 1200 chars to keep prompts reasonable
        if text and len(text) > 1200:
            text = text[:1200] + "...(truncated)"
        contexts.append(f"Source: {source}, id:{res.get('id')}\\n{text}")
    context_text = "\\n\\n".join(contexts) if contexts else "No relevant context found."
    prompt = PROMPT_TEMPLATE.replace("{context}", context_text).replace("{question}", req.question)
# 3) build context (improved)

    # Build contexts including text; apply simple summarization/truncation to respect token budget.
    contexts = []
    total_chars = 0
    CHAR_BUDGET = 3000  # total characters to include across all contexts
    for res in results:
        md = res.get("metadata", {}) or {}
        source = md.get("source", "unknown")
        text = md.get("text", "") or ""
        # simple summarizer: if text is longer than 800 chars, keep first 400 + last 200
        if len(text) > 800:
            text = text[:400] + "\n...(middle truncated)...\n" + text[-200:]
        # if adding this would exceed budget, skip or truncate further
        if total_chars + len(text) > CHAR_BUDGET:
            remaining = max(0, CHAR_BUDGET - total_chars)
            if remaining <= 0:
                break
            text = text[:remaining] + "...(truncated by budget)"
        contexts.append({"source": source, "id": res.get("id"), "text": text})
        total_chars += len(text)
    if contexts:
        # create numbered context blocks with simple citation markers
        ctx_blocks = []
        for i, c in enumerate(contexts, start=1):
            ctx_blocks.append(f"[{i}] Source: {c['source']}, id:{c['id']}\n{c['text']}")
        context_text = "\n\n".join(ctx_blocks)
    else:
        context_text = "No relevant context found."
    # Build final prompt with citations instruction
    prompt = PROMPT_TEMPLATE.replace("{context}", context_text).replace("{question}", req.question)
    prompt = "You are an assistant that cites sources. When you use information from the context, add citation markers like [1], [2] corresponding to the source list.\\n\\n" + prompt

# 4) call LLM
    r3 = requests.post(LLM_URL, json={"prompt": prompt, "max_tokens": 512}, timeout=60)
    if r3.status_code != 200:
        raise HTTPException(status_code=502, detail="LLM service error")
    ans = r3.json().get("text", "")
    return {"answer": ans, "retrieved": results}
