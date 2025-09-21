
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import os, json
import numpy as np
from threading import Lock

# Optional Chroma support: set USE_CHROMA=1 to use chromadb local instance (requires chromadb package)
USE_CHROMA = os.getenv("USE_CHROMA", "0") == "1"

if USE_CHROMA:
    try:
        import chromadb
        from chromadb.config import Settings
        from chromadb.utils import embedding_functions
    except Exception as e:
        raise RuntimeError("Chroma requested (USE_CHROMA=1) but chromadb not installed: " + str(e))

DATA_DIR = "vector_db_data"
META_FILE = os.path.join(DATA_DIR, "meta.json")
DIM = 384

os.makedirs(DATA_DIR, exist_ok=True)

app = FastAPI(title="Vector DB (Annoy/Chroma)")

lock = Lock()

if USE_CHROMA:
    # simple chroma client using default local settings
    client = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet", persist_directory=DATA_DIR))
    collection_name = os.getenv("CHROMA_COLLECTION", "rag_docs")
    if collection_name in [c.name for c in client.list_collections()]:
        collection = client.get_collection(collection_name)
    else:
        collection = client.create_collection(name=collection_name)
    # store metadata in collection metadatas as usual
else:
    from annoy import AnnoyIndex
    t = AnnoyIndex(DIM, "angular")
    # load previous meta if exists
    meta = {}
    next_id = 0
    index_built = False
    if os.path.exists(META_FILE):
        with open(META_FILE, "r", encoding="utf-8") as f:
            meta = json.load(f)
        if meta:
            next_id = max(int(k) for k in meta.keys()) + 1
    index_path = os.path.join(DATA_DIR, "annoy.index")
    if os.path.exists(index_path):
        try:
            t.load(index_path)
            index_built = True
        except:
            index_built = False

class UpsertItem(BaseModel):
    id: str
    vector: List[float]
    metadata: Dict[str, Any] = {}

class QueryRequest(BaseModel):
    vector: List[float]
    top_k: int = 3

@app.post("/upsert")
def upsert(items: List[UpsertItem]):
    with lock:
        if USE_CHROMA:
            ids = [it.id for it in items]
            embeddings = [it.vector for it in items]
            metadatas = [it.metadata for it in items]
            # upsert into chroma collection
            collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas)
            client.persist()
            return {"inserted": len(items)}
        else:
            global index_built
            for it in items:
                internal_id = int(hash(it.id) & 0x7fffffff) % (2**31-1)
                if len(it.vector) != DIM:
                    raise HTTPException(status_code=400, detail=f"vector must be length {DIM}")
                t.add_item(internal_id, np.array(it.vector, dtype=np.float32))
                meta[str(internal_id)] = {"id": it.id, "metadata": it.metadata}
            t.build(10)
            t.save(os.path.join(DATA_DIR, "annoy.index"))
            with open(META_FILE, "w", encoding='utf-8') as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
            index_built = True
            return {"inserted": len(items)}

@app.post("/query")
def query(q: QueryRequest):
    if USE_CHROMA:
        results = collection.query(query_embeddings=[q.vector], n_results=q.top_k, include=['metadatas','ids','distances'])
        out = []
        for ids, dists, metads in zip(results['ids'], results['distances'], results['metadatas']):
            for id_, dist, md in zip(ids, dists, metads):
                out.append({"id": id_, "metadata": md, "distance": dist})
        return {"results": out}
    else:
        if not index_built:
            return {"results": []}
        ids, distances = t.get_nns_by_vector(q.vector, q.top_k, include_distances=True)
        results = []
        for iid, dist in zip(ids, distances):
            m = meta.get(str(iid), {})
            results.append({"id": m.get("id"), "metadata": m.get("metadata"), "distance": dist})
        return {"results": results}
