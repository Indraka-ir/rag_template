
"""
Reads pipeline/output/chunks.json, calls embedding_service /embed,
then calls vector_db /upsert to store vectors and metadata.
"""
import os, json, requests, time
from tqdm import tqdm

CONFIG_FILE = "config/config.json"
with open(CONFIG_FILE, "r") as f:
    cfg = json.load(f)

EMBED_URL = cfg["embedding_service_url"].rstrip("/") + "/embed"
VECTOR_URL = cfg["vector_db_url"].rstrip("/") + "/upsert"
INPUT = "pipeline/output/chunks.json"
BATCH = 32

with open(INPUT, "r", encoding="utf-8") as f:
    chunks = json.load(f)

for i in range(0, len(chunks), BATCH):
    batch = chunks[i:i+BATCH]
    texts = [c["text"] for c in batch]
    r = requests.post(EMBED_URL, json={"texts": texts}, timeout=60)
    r.raise_for_status()
    embs = r.json()["embeddings"]
    upsert_items = []
    for c, emb in zip(batch, embs):
        upsert_items.append({"id": c["id"], "vector": emb, "metadata": {"source": c["source"], "text": c["text"], **c.get("meta", {})}})
    r2 = requests.post(VECTOR_URL, json=upsert_items, timeout=60)
    r2.raise_for_status()
    print(f"Upserted batch {i}..{i+len(batch)}")
    time.sleep(0.1)
print("Done.")
