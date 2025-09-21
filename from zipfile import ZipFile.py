from zipfile import ZipFile
from pathlib import Path

zip_path = Path("rag_template_all.zip")
out_dir  = Path("./")

out_dir.mkdir(parents=True, exist_ok=True)
with ZipFile(zip_path, "r") as zf:
    zf.extractall(out_dir)
