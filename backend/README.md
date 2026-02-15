# Health Insights AI Assistance - Project Summary

## What Was Done

- **FastAPI Backend Setup:**
  - Built a FastAPI server for health-related Q&A and document analysis.
  - Organized code into modular folders: `agents`, `api/routes`, `core`, `app`, `config`, etc.

- **LLM Integration:**
  - Integrated LangChain with Ollama for local LLM responses.
  - Added a MockLLM fallback for development/testing without Ollama.
  - Automatic fallback to MockLLM if Ollama is unavailable or slow.

- **Session Management:**
  - Implemented session handling using Redis.
  - Created MockRedis alternative for local development (no Redis required).

- **Endpoints Created:**
  - `POST /api/followup`: Handles follow-up health questions, returns LLM output.
  - `GET /api/test-followup`: Serves a browser-based test form for easy manual testing.
  - `GET /api/health`: Health check endpoint.

- **Development Infrastructure:**
  - Startup scripts for Ollama and FastAPI server.
  - Environment variable toggles for mock mode (`USE_MOCK_LLM=true`).
  - HTML test page for browser-based manual testing.

- **Testing:**
  - Verified LLM responses via Python scripts and browser form.
  - Ensured fallback to MockLLM when Ollama is unavailable.

- **Performance Notes:**
  - First LLM request may take 2-3 minutes (model loading).
  - Subsequent requests are faster.
  - MockLLM provides instant responses for development.

---

## Technical Steps & Commands

### 1. Start Ollama (LLM Backend)
Open a terminal and run:
```bash
ollama run llama3
```
*For faster responses, use:*
```bash
ollama run gemma2:2b
```

### 2. Start FastAPI Server
Open another terminal and run:
```powershell
cd "d:\nus-iss\Health-Insights-AI-Assistance\backend"
python run.py
```

### 3. Access the Test Page
Open your browser and go to:
```
http://127.0.0.1:8000/api/test-followup
```

### 4. Use MockLLM (Instant Responses, No Ollama Needed)
Set the environment variable before starting the server:
```powershell
$env:USE_MOCK_LLM="true"
cd "d:\nus-iss\Health-Insights-AI-Assistance\backend"
python run.py
```

---

## Troubleshooting Tips

### Ollama is slow
- First request takes 2-3 minutes (model loading).
- Subsequent requests are faster (~10-30 seconds).
- If too slow, use `USE_MOCK_LLM=true` for instant responses.
- Try a smaller model: `ollama run gemma2:2b` or `ollama run gemma:2b`.

### Server won't start
- Make sure you're in the backend directory.
- Check that port 8000 is not in use.
- Run: `python run.py` directly to see errors.
- If you see `ModuleNotFoundError`, install missing packages:
  ```powershell
  pip install -r requirements.txt
  ```

### Ollama won't connect
- Make sure Ollama is running on http://127.0.0.1:11434.
- The system will auto-fallback to MockLLM if Ollama is unavailable.
- Check Ollama logs for errors.

### Redis not available
- MockRedis is used by default for development.
- No need to install Redis unless running in production.

### Health check
- Test server status at:
  ```
  http://127.0.0.1:8000/api/health
  ```

---

## Project Structure

- `backend/` - Main backend code
  - `main.py` - FastAPI app entry point
  - `run.py` - Startup script for server
  - `core/llm.py` - LLM integration and fallback logic
  - `core/mock_redis.py` - Mock Redis implementation
  - `agents/followup_agent.py` - Follow-up agent logic
  - `api/routes/chat.py` - API endpoints
  - `prompts/` - Prompt templates

---

## For Next Laptop Restart

Just run:
```powershell
ollama run llama3
# or
ollama run gemma2:2b

cd "d:\nus-iss\Health-Insights-AI-Assistance\backend"
python run.py
```

Or use MockLLM for instant responses:
```powershell
$env:USE_MOCK_LLM="true"
cd "d:\nus-iss\Health-Insights-AI-Assistance\backend"
python run.py
```

---

## Useful Links
- Test page: http://127.0.0.1:8000/api/test-followup
- Health check: http://127.0.0.1:8000/api/health
- API endpoint: POST /api/followup

---

# Project Setup & Usage

## 📦 Package Installation
When installing new packages, remember to keep both `pip` and `uv` in sync:
```bash
pip install <package-name>
uv add <package-name>
```
## Run Project Locally
1) Create .env file and add OPENAI_API_KEY 
2) Change directory to /backend
3) Run: uv sync
4) Run: uv run uvicorn main:app --reload --log-level debug
5) Ensure local redis is running on port 6379
Testing using Swagger UI: http://localhost:8000/docs

## Ollama terminal: ollama run llama3 or ollama run gemma2:2b
## Server terminal: cd backend then python run.py
## http://127.0.0.1:8000/api/test-followup