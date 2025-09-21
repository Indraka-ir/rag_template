
from fastapi import FastAPI
from pydantic import BaseModel
import os
import openai

app = FastAPI(title="LLM API Gateway")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_KEY:
    openai.api_key = OPENAI_KEY

class LLMReq(BaseModel):
    prompt: str
    max_tokens: int = 256

@app.post("/generate")
def generate(req: LLMReq):
    # If OPENAI_API_KEY is set, call OpenAI; else return a simple stub
    if OPENAI_KEY:
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role":"user","content":req.prompt}],
            max_tokens=req.max_tokens,
            temperature=0.2,
        )
        text = resp["choices"][0]["message"]["content"]
        return {"text": text}
    # stub:
    return {"text": "LLM stub: could not call provider because OPENAI_API_KEY is not set. Prompt received:\\n\\n" + req.prompt[:1000]}
