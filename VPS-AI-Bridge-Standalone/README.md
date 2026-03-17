# VPS-AI-Bridge

A standalone, lightweight Python FastAPI server that acts as an OpenAI-compatible proxy. It routes inference requests to high-speed providers (Groq, SambaNova, OpenRouter) based on custom aliases.

This is highly useful for running AI Agent frameworks (like MetaGPT or LangGraph) on low-resource environments (like Oracle ARM VPS) where running heavy local SLMs (like Llama 3) via Ollama is too slow.

## Priority Routing Logic
The bridge intercepts requests sent to `/v1/chat/completions` and redirects them based on the requested model "alias":
- `"heavy"` or `"405b"` -> Routes to OpenRouter (Llama 3.1 405B)
- `"precision"` or `"deepseek-coder"` -> Routes to OpenRouter (DeepSeek R1)
- `"architect"`, `"fast"`, `"llama-3"` -> Routes to SambaNova (Llama 3.3 70B), falls back to Groq.
- Default -> Routes to Groq (Llama 3.3 70B).

## Usage & Deployment

This application is designed to be easily integrated into Docker Compose stacks next to orchestration engines.

### 1. Standalone Docker Deployment
To run just the bridge API locally or on a VPS:

```bash
# Build the image
docker build -t vps-ai-bridge .

# Run the container (ensure you pass your API keys)
docker run -d -p 5000:5000 \
  -e GROQ_API_KEY="your_groq_key" \
  -e OPENROUTER_API_KEY="your_or_key" \
  -e SAMBANOVA_API_KEY="your_sn_key" \
  vps-ai-bridge
```
Your OpenAI compatible endpoint is now live at `http://localhost:5000/v1`

### 2. Deployment via Docker Compose (Portainer)
Usually, you deploy this alongside your AI framework. In your `docker-compose.yml`, reference this repository to build dynamically:

```yaml
vps-ai-bridge:
  build: 
    context: https://github.com/YourName/VPS-AI-Bridge.git
  container_name: vps-ai-bridge
  restart: unless-stopped
  ports:
    - "5000:5000"
  environment:
    - GROQ_API_KEY=${GROQ_API_KEY}
    - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
    - SAMBANOVA_API_KEY=${SAMBANOVA_API_KEY}
```

### 3. Client Configuration
To point AutoGen, MetaGPT, or LangChain to this bridge, set the `api_type` to `openai` and change the `base_url`:

```python
# Example Client Config
llm_config = {
    "api_type": "openai",
    "base_url": "http://<bridge-ip>:5000/v1",
    "api_key": "sk-dummy-key", # Required by strict clients, but ignored by bridge
    "model": "architect" # Passes the alias to the bridge router
}
```
