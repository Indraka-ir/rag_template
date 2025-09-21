
"""
Loader + chunker with support for .txt, .pdf, .docx
"""
import os, json, hashlib
from pathlib import Path
from tqdm import tqdm

INPUT_DIR = "pipeline/input"
OUTPUT_DIR = "pipeline/output"
CHUNK_SIZE = 800  # characters
CHUNK_OVERLAP = 100

os.makedirs(OUTPUT_DIR, exist_ok=True)
chunks = []

def chunk_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    start = 0
    n = len(text)
    while start < n:
        end = min(start + size, n)
        yield text[start:end]
        if end == n:
            break
        start = max(0, end - overlap)

def extract_text_from_pdf(path):
    try:
        from pdfminer.high_level import extract_text
        return extract_text(path)
    except Exception as e:
        print("PDF extraction failed:", e)
        return ""

def extract_text_from_docx(path):
    try:
        import docx
        doc = docx.Document(path)
        texts = [p.text for p in doc.paragraphs]
        return "\n".join(texts)
    except Exception as e:
        print("DOCX extraction failed:", e)
        return ""

for p in Path(INPUT_DIR).glob("*"):
    if p.is_file():
        suffix = p.suffix.lower()
        if suffix == ".txt":
            try:
                text = p.read_text(encoding='utf-8')
            except:
                text = p.read_text(encoding='latin-1')
        elif suffix == ".pdf":
            text = extract_text_from_pdf(str(p))
        elif suffix == ".docx":
            text = extract_text_from_docx(str(p))
        else:
            # attempt to read as text
            try:
                text = p.read_text(encoding='utf-8')
            except:
                text = p.read_text(encoding='latin-1')
        for i, c in enumerate(chunk_text(text)):
            id_raw = f"{p.name}-{i}"
            cid = hashlib.sha1(id_raw.encode()).hexdigest()
            chunks.append({"id": cid, "text": c, "source": p.name, "meta": {"chunk_id": i}})
# write
with open(os.path.join(OUTPUT_DIR, "chunks.json"), "w", encoding="utf-8") as f:
    json.dump(chunks, f, ensure_ascii=False, indent=2)
print(f"Wrote {len(chunks)} chunks to {os.path.join(OUTPUT_DIR, 'chunks.json')}")
