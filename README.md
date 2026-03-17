# AITeamOrchestration

A self-hosted, multi-agent AI orchestration environment designed to run on resource-constrained environments (like Oracle A1.Flex ARM VPS) using external routed intelligence.

This repository pairs with the [VPS-AI-Bridge](https://github.com/AliRaza/VPS-AI-Bridge) to provide a complete MetaGPT and Web UI stack.

## Components
1. **MetaGPT Backend**: Orchestrates the software agents (Architect, Dev, QA, etc.).
2. **MetaGPT Web UI**: A browser-based interface to interact with MetaGPT.
3. **VPS-AI-Bridge Integration**: Proxies OpenAI-compatible requests to fast inference engines like Groq, SambaNova, and OpenRouter without relying on heavy local SLMs.

## Deployment Instructions (Oracle VPS via Portainer)

### 1. Prerequisites
- Docker and Portainer installed on your VPS.
- You have pushed this repository and your `VPS-AI-Bridge` repository to GitHub.
- Valid API Keys for Groq, OpenRouter, and SambaNova.

### 2. Configure the Repository URLs
Before starting the stack, ensure you have updated the GitHub repository URLs inside the `infrastructure/docker-compose.yml` file under the `git-sync` service command.
- `YOUR_ORCHESTRATOR_REPO_URL` 
- `YOUR_BRIDGE_REPO_URL`

### 3. Deploy in Portainer
There are two ways to deploy this in Portainer:

**Method A: Custom Stack Deploy (Recommended)**
1. Open your Portainer Dashboard.
2. Go to **Stacks** > **Add stack**.
3. Name it e.g., `ai-orchestrator`.
4. Choose **Repository** build method (or simply copy the contents of `infrastructure/docker-compose.yml` into the Web editor).
5. In the **Environment Variables** section below the editor, add your required keys:
   - `GROQ_API_KEY=your_key`
   - `OPENROUTER_API_KEY=your_key`
   - `SAMBANOVA_API_KEY=your_key`
6. Click **Deploy the stack**.

**Method B: Command Line (docker-compose)**
If you prefer SSH, clone this repository and run:
```bash
cd infrastructure
# Set your environment variables
export GROQ_API_KEY="..."
export OPENROUTER_API_KEY="..."
export SAMBANOVA_API_KEY="..."
# Start the stack
docker-compose up -d --build
```

### 4. Usage
Once deployed, the containers will automatically sync the latest code from GitHub.
- Access the MetaGPT Web UI by navigating to: `http://<YOUR_VPS_IP>:8080`
- To run a prompt manually via CLI:
  ```bash
  docker exec -it metagpt-backend python startup.py "your prompt here"
  ```

Outputs (generated code and diagrams) will be saved in the `workspace` volume, which is accessible from both the UI and the backend container.
