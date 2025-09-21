
import streamlit as st
import requests
import json
from pathlib import Path

st.set_page_config(page_title="RAG Chat", layout="centered")
st.title("RAG Chat")

with open("config/config.json","r") as f:
    cfg = json.load(f)
RAG_URL = "http://localhost:8083/ask"

if "history" not in st.session_state:
    st.session_state.history = []

q = st.text_input("Ask a question", value="", max_chars=1000)
if st.button("Send"):
    if not q.strip():
        st.warning("Type a question.")
    else:
        res = requests.post(RAG_URL, json={"question": q}, timeout=60)
        if res.status_code == 200:
            data = res.json()
            st.session_state.history.append((q, data["answer"], data.get("retrieved", [])))
        else:
            st.error(f"Error: {res.text}")

for q,a,ret in reversed(st.session_state.history):
    st.markdown(f"**Q:** {q}")
    st.markdown(f"**A:** {a}")
    if ret:
        st.markdown("**Retrieved:**")
        for r in ret:
            st.markdown(f"- {r}")
    st.write("---")
