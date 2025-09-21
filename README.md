Minimal Retrieval-Augmented Generation (RAG) template
---------------------------------------------------

This project is a lightweight, configurable RAG example you can run locally,
inspect, adapt, and push to GitLab. It is intentionally simple and **contains no
references to any proprietary product**. Use this as a starting point.

Services:
- embedding_service: FastAPI that returns sentence-transformers embeddings.
- vector_db: FastAPI that stores embeddings and metadata, provides nearest-neighbor search (Annoy).
- load_and_chunk: Script to split input text files into chunks (produces pipeline/output/chunks.json).
- embed_and_store: Script to call embedding_service for chunks and upsert into vector_db.
- llm_api: FastAPI wrapper to call OpenAI (if OPENAI_API_KEY set) or return a basic stub response.
- rag_orchestrator: FastAPI that ties everything together: embeds a question, retrieves context, builds prompt, calls llm_api.
- rag_ui: Streamlit frontend for chatting with the RAG system.

Quickstart (local):
1. Create a Python venv and install dependencies:
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

2. Start services (each runs on its own port):
   uvicorn embedding_service.app:app --reload --port 8081
   uvicorn vector_db.app:app --reload --port 8001
   uvicorn llm_api.app:app --reload --port 8082
   uvicorn rag_orchestrator.app:app --reload --port 8083

3. Index documents:
   - Put your text/PDF files into pipeline/input
   - python load_and_chunk.py
   - python embed_and_store.py

4. Open UI:
   streamlit run rag_ui/app.py

Configuration:
- Edit the config files in `config/` to change ports, models, collection name, prompt template, etc.
- Never hardcode API keys in config files. Use environment variables for secrets.

Notes:
- This is a minimal, educational example. For production, replace Annoy with a production-grade vector DB, secure services, add auth, and use a managed LLM provider.


## New features added

- Retrieved chunk texts are now included in vector DB metadata and will be placed into prompts by the orchestrator.
- Kubernetes manifests for each service are in the `k8s/` directory (starter templates).
- A Helm chart scaffold is in `helm/rag-chart/`.
- A GitLab CI pipeline template is provided as `.gitlab-ci.yml`.

See the `k8s/README.md` for notes on adapting manifests for your environment.


## All-up update

This version includes:
- Optional Chroma vector DB support (set USE_CHROMA=1 and install chromadb).
- Dockerfiles for each service under <service>/Dockerfile. CI builds these images.
- GitLab CI updated to build and push per-service images and deploy k8s manifests.
- k8s manifests updated to reference per-service images pushed by CI.
- Loader supports PDF and DOCX extraction using pdfminer.six and python-docx.
- Orchestrator prompt builder improved: simple summarization, char-budgeting, and citation markers.

Follow README earlier steps; ensure you set correct CI variables (CI_REGISTRY credentials, KUBE_CONFIG_BASE64).
