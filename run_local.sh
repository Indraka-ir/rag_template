#!/usr/bin/env bash
# start services (simplest local approach)
uvicorn embedding_service.app:app --reload --port 8081 &
uvicorn vector_db.app:app --reload --port 8001 &
uvicorn llm_api.app:app --reload --port 8082 &
uvicorn rag_orchestrator.app:app --reload --port 8083 &
echo "Started services. Run streamlit separately: streamlit run rag_ui/app.py"
