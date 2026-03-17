from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Union, Dict, Any
import os
import requests
import json
import uuid
import time

app = FastAPI(title="VPS-AI-Bridge", description="OpenAI-compatible wrapper for Alamia-AI routing logic")

class UniversalBridge:
    def __init__(self):
        self.keys = {
            "groq": os.getenv("GROQ_API_KEY"),
            "openrouter": os.getenv("OPENROUTER_API_KEY"),
            "sambanova": os.getenv("SAMBANOVA_API_KEY"),
            "local": "http://localhost:11434/api/generate"
        }

    def call_api(self, provider, url, headers, data, timeout=60):
        try:
            r = requests.post(url, headers=headers, json=data, timeout=timeout)
            if r.status_code == 200:
                # Need to return full raw dict so FastAPI can stream/reconstruct OpenAI response
                return r.json()
            elif r.status_code == 429:
                raise HTTPException(status_code=429, detail=f"ERROR: {provider} Quota Exceeded (429)")
            else:
                raise HTTPException(status_code=r.status_code, detail=f"ERROR: {provider} API returned {r.status_code}: {r.text[:100]}")
        except requests.exceptions.Timeout:
            raise HTTPException(status_code=504, detail=f"ERROR: {provider} Connection Timeout")
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"ERROR: {provider} unexpected error: {str(e)}")

    def call_groq(self, messages, model="llama-3.3-70b-versatile", **kwargs):
        if not self.keys["groq"]: raise HTTPException(status_code=500, detail="ERROR: GROQ_API_KEY missing")
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.keys['groq']}", "Content-Type": "application/json"}
        data = {"model": model, "messages": messages}
        
        # pass through optional kwargs like temperature
        for k in ["temperature", "max_tokens", "top_p", "response_format"]:
            if k in kwargs and kwargs[k] is not None:
                data[k] = kwargs[k]
                
        return self.call_api("Groq", url, headers, data)

    def call_openrouter(self, messages, model="meta-llama/llama-3.1-405b:free", **kwargs):
        if not self.keys["openrouter"]: raise HTTPException(status_code=500, detail="ERROR: OPENROUTER_API_KEY missing")
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.keys['openrouter']}",
            "HTTP-Referer": "https://github.com/antigravity",
            "Content-Type": "application/json"
        }
        data = {"model": model, "messages": messages}
        for k in ["temperature", "max_tokens", "top_p", "response_format"]:
            if k in kwargs and kwargs[k] is not None:
                data[k] = kwargs[k]
        return self.call_api("OpenRouter", url, headers, data)

    def call_sambanova(self, messages, model="Meta-Llama-3.3-70B-Instruct", **kwargs):
        if not self.keys["sambanova"]: raise HTTPException(status_code=500, detail="ERROR: SAMBANOVA_API_KEY missing")
        url = "https://api.sambanova.ai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.keys['sambanova']}", "Content-Type": "application/json"}
        data = {"model": model, "messages": messages}
        for k in ["temperature", "max_tokens", "top_p", "response_format"]:
            if k in kwargs and kwargs[k] is not None:
                data[k] = kwargs[k]
        return self.call_api("SambaNova", url, headers, data)

    def route(self, alias_or_model, messages, **kwargs):
        alias = alias_or_model.lower()
        
        # Determine Priority
        if alias == "heavy" or "405b" in alias:
            return self.call_openrouter(messages, "meta-llama/llama-3.1-405b:free", **kwargs)
        
        if alias == "precision" or "deepseek" in alias:
            # We map "deepseek-coder" requests from MetaGPT here as well
            return self.call_openrouter(messages, "deepseek/deepseek-r1", **kwargs)

        # Daily Driver (Try SambaNova first for speed/capacity if key exists)
        if self.keys["sambanova"] and (alias == "architect" or alias == "fast" or "llama-3" in alias):
            try:
                # By default try sambanova
                res = self.call_sambanova(messages, "Meta-Llama-3.3-70B-Instruct", **kwargs)
                return res
            except Exception as e:
                # if sambanova fails, fallback to groq
                print(f"Fallback due to SambaNova error: {e}")
                pass

        # Fallback to Groq for everything else (or if SambaNova failed/missing key)
        return self.call_groq(messages, "llama-3.3-70b-versatile", **kwargs)

bridge = UniversalBridge()

class ChatMessage(BaseModel):
    role: str
    content: str
    
class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    stream: Optional[bool] = False
    response_format: Optional[Dict[str, str]] = None

@app.get("/v1/models")
async def get_models():
    # Return a mocked models list to satisfy clients calling /v1/models
    models = ["heavy", "precision", "fast", "llama-3.3-70b-versatile", "deepseek-coder", "gpt-4"]
    return {
        "object": "list",
        "data": [{"id": m, "object": "model", "created": int(time.time()), "owned_by": "vps-ai-bridge"} for m in models]
    }

@app.post("/v1/chat/completions")
async def chat_completions(req: ChatCompletionRequest):
    # MetaGPT uses strict OpenAI types, we intercept them and pass to our bridge
    messages = [{"role": m.role, "content": m.content} for m in req.messages]
    
    # We pass the requested model as the 'alias' to the bridge logic
    response_json = bridge.route(
        alias_or_model=req.model, 
        messages=messages,
        temperature=req.temperature,
        max_tokens=req.max_tokens,
        top_p=req.top_p,
        response_format=req.response_format
    )
    
    # Returning the JSON response directly. Because our bridge routes to OpenAI-compatible
    # endpoints (Groq, OpenRouter, SambaNova), the returned JSON is ALREADY in the correct
    # OpenAI format, meaning we just proxy it straight back to MetaGPT!
    return response_json

if __name__ == "__main__":
    import uvicorn
    # Local test run
    uvicorn.run(app, host="0.0.0.0", port=5000)
