# Nashmi — Government Services Requirements Gathering & Platform

A complete, self-contained README for the Nashmi repository. This project provides:

- An interactive requirements gathering chatbot (CLI + Flask web UI) that converses in Arabic to collect structured service requirements.
- A Service Builder that produces a standard text document and JSON representation for each service.
- An optional pipeline that generates a small FastAPI backend + HTML frontend for each service and a central platform (FastAPI) to host generated services.

This README explains how the system is organized, how to install dependencies, how to run both primary flows, details of the REST endpoints exposed by the gathering UI, where outputs are stored, troubleshooting tips, security guidance, and recommended next steps.

---

Table of Contents
- Overview
- Repository structure
- Prerequisites
- Installation
- Configuration (API key and environment variables)
- How to run
  - CLI requirements gathering
  - Flask web UI (browser)
  - Platform (run_platform.py)
- API reference (Flask chat UI)
- Generated artifacts and folders
- Troubleshooting
- Security and deployment notes
- Recommended improvements / next steps
- Contributing
- License

---

Overview
--------
Nashmi is an experimental tool designed to help government teams capture service requirements in a structured manner. The tool uses an AI-assisted chat flow (via Google Generative AI) to ask concise Arabic questions, validates user answers, stores them in a canonical JSON template, and generates a human-readable service document.

Optionally, a pipeline will use the gathered JSON to generate a minimal service implementation (backend + frontend) under `agents/generated_services`. The central FastAPI platform (`app/main.py`) will auto-discover generated services and present them in the platform dashboard.

Repository structure (key files)
--------------------------------
- `run_platform.py` — Start the central platform (FastAPI backend + static frontend server).
- `requirements.txt` — Minimal required Python packages (Flask, flask-cors, google-generativeai). See Installation section to add missing packages.
- `requirements_agents/`
  - `app.py` — Flask web server version of the chat-based requirements collector.
  - `main.py` — CLI version to run the chat-based collector in terminal.
  - `main2.py` — alternative Flask-based approach (present in repo as a reference).
  - `chat_agent.py` — ChatAgent and ValidatorAgent implementations (uses google-generativeai).
  - `service_builder.py` — Produces `serviceN.txt` and `serviceN.json`, manages `service_counter.txt`.
  - `prompts.py` — `service_intake_form` template and prompt/context data for questions.
  - `chatbot_ui.html`, `chat_ui.html` — UI files used by the Flask web app.
  - Example service JSON/TXT files (`service1.json`, `service1.txt`, ...).
- `app/main.py` — Central FastAPI platform that mounts the frontend and generated services and exposes `/api/system/services`.
- `agents/` — Pipeline and orchestration code that transforms service JSON into a generated service (`agents/main.py`, `agents/orchestrator.py`, `agents/backend.py`, `agents/frontend.py`).

Prerequisites
-------------
- Python 3.10+ (3.10/3.11 recommended)
- pip
- A Google Generative AI API key (for `google-generativeai` usage)

Installation (PowerShell)
-------------------------
1. Create and activate a virtual environment (recommended):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt fastapi uvicorn
```

Note: `requirements.txt` in the repo contains the core libraries for the requirements agent (Flask + google generative sdk). The platform also requires `fastapi` and `uvicorn`, therefore we recommend installing them as shown above.

Configuration (API key and environment variables)
-------------------------------------------------
The code currently includes inline `api_key` variables in several places (for convenience during development). For security and production use, do not leave API keys in source control. Instead set an environment variable and update the code to read it.

Recommended environment variable name: `GENAI_API_KEY`

Set the key for the current PowerShell session:

```powershell
$env:GENAI_API_KEY = "YOUR_GOOGLE_GENERATIVE_AI_API_KEY"
```

To persist the variable for future sessions (Windows):

```powershell
setx GENAI_API_KEY "YOUR_GOOGLE_GENERATIVE_AI_API_KEY"
```

Files to update (optional but recommended):
- `requirements_agents/app.py` — replace hardcoded `api_key = '...'` with `os.getenv('GENAI_API_KEY')`.
- `requirements_agents/main.py` — same replacement.
- `agents/main.py` — look for `API_KEY = "..."` and replace with `os.getenv('GENAI_API_KEY')`.
- `requirements_agents/chat_agent.py` and `requirements_agents/service_builder.py` — ensure they receive `api_key` from callers or from environment.

How to run
----------
All commands below assume you are in the repository root (`D:\d\nashmi`) and have activated the virtual environment.

1) CLI requirements gathering (terminal)

```powershell
python .\requirements_agents\main.py
```

Behavior:
- Starts an interactive Arabic chat in the terminal.
- Asks questions derived from `prompts.service_intake_form`.
- Uses `ValidatorAgent` to accept/reject answers via Google Generative AI.
- On completion, `ServiceBuildingAgent` generates:
  - `serviceN.txt` — human-readable document
  - `serviceN.json` — structured JSON for the pipeline
  - `service_counter.txt` — persists index N
- The script optionally runs `run_pipeline` from `agents.main` if available.

2) Flask web UI (browser)

Start the Flask-based web UI (serves `chatbot_ui.html` and provides endpoints):

```powershell
python .\requirements_agents\app.py
```

Open a browser and navigate to: `http://127.0.0.1:5000`

Important:
- `requirements_agents/app.py` checks that `chatbot_ui.html` exists in the same folder and that `api_key` is set (or updated to read `GENAI_API_KEY`).
- Endpoints are documented in the API reference section below.

3) Platform: start the central platform (FastAPI) and the simple frontend server

The project includes `run_platform.py` which starts two processes:
- A uvicorn FastAPI server (serving `app.main:app`) on port `8000`.
- A simple static server (Python `http.server`) serving the `frontend` folder on port `3000`.

Run it from the repo root:

```powershell
python .\run_platform.py
```

It will open the default browser to `http://127.0.0.1:3000/index.html`.

API reference (requirements_agents Flask UI)
-------------------------------------------
Base URL (default): `http://127.0.0.1:5000`

- GET `/` — Serves the `chatbot_ui.html` front-end.
- GET `/init` — Initialize a new chat session.
  - Response (success): `{ "status": "success", "message": "<greeting + first question>" }`
- POST `/chat` — Submit a user answer to the current question.
  - Request JSON: `{ "message": "user reply text" }`
  - Response cases:
    - If session inactive: 400 with a JSON error message.
    - If validation fails: returns object with `status: "success"` and `response` explaining the invalid answer (the code returns invalid as non-blocking but instructs user to retry).
    - If valid and more questions remain:
      ```json
      { "status": "success", "response": "<next question>", "completed": false, "progress": { ... } }
      ```
    - If this was the final answer:
      ```json
      { "status": "success", "response": "...", "completed": true }
      ```
- GET `/status` — Returns current session state and progress. Example:

```json
{ "active": true, "initialized": true, "progress": { "total": 40, "completed": 5, "remaining": 35, "percentage": 12 } }
```

- POST `/reset` — Reset the current session and initialize a new one.

Generated artifacts & where to find them
---------------------------------------
- `serviceN.txt` — Text document produced by `ServiceBuildingAgent.save_to_file()`.
- `serviceN.json` — JSON used by the pipeline, created alongside the text document.
- `service_counter.txt` — Stores the last used index N.
- Pipeline output (if you run `agents.main.run_pipeline`):
  - New folder under `agents/generated_services/` named `service_<sanitized_service_name>` containing:
    - `backend.py` — minimal FastAPI backend for that service
    - `app.html` — single-page frontend for the service
  - The platform (`app/main.py`) will auto-discover and mount these services at `/view/<service_folder>/app.html` and list them at `/api/system/services`.

Troubleshooting
---------------
- Missing `chatbot_ui.html` when running `requirements_agents/app.py`:
  - Place `chatbot_ui.html` in `requirements_agents/` or run the script with working directory set to that folder.

- `index.html` not found when running `run_platform.py`:
  - Ensure `frontend/index.html` exists at the repo root (`D:\d\nashmi\frontend\index.html`).

- `uvicorn` import/run issues:
  - Install `uvicorn` with `pip install uvicorn`.

- API key/auth problems with `google-generativeai`:
  - Ensure `GENAI_API_KEY` is set and valid. Check network connectivity.
  - If you get model/permission errors, verify your Google account and API entitlements.

- Pipeline writes files to unexpected locations:
  - `agents/main.py` contains path assembly logic. Inspect for any absolute paths (e.g., `r'D:\d\nashmi\agents\generated_services'`) and adjust to your environment or make them relative.

Security & deployment notes
--------------------------
- Do not commit API keys to source control. Replace hardcoded keys with `os.getenv('GENAI_API_KEY')`.
- For production:
  - Run FastAPI with multiple uvicorn workers behind a reverse proxy (Nginx) and TLS.
  - Restrict CORS to trusted origins (currently set to `*` in `app/main.py`).
  - Use authentication/authorization for the platform and service endpoints.
  - Consider storing service artifacts in a database or object storage rather than repository folders.

Recommended improvements / next steps
------------------------------------
- Add `fastapi` and `uvicorn` to `requirements.txt`.
- Replace inline API keys with environment lookups.
- Make pipeline path handling fully relative and portable.
- Add unit tests (smoke tests for ChatAgent and ServiceBuildingAgent).
- Add a small CI job to run linting and basic unit tests.
