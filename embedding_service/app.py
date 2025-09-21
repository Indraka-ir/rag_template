
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from sentence_transformers import SentenceTransformer
import numpy as np

app = FastAPI(title="Embedding Service")
model = SentenceTransformer("all-MiniLM-L6-v2")

class Texts(BaseModel):
    texts: List[str]

@app.post("/embed")
def embed(payload: Texts):
    embs = model.encode(payload.texts, show_progress_bar=False, convert_to_numpy=True)
    # convert to list for JSON serialization
    return {"embeddings": [emb.tolist() for emb in embs]}
