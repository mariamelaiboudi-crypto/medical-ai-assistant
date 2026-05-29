# Medical AI Assistant

A multi-agent clinical consultation system built with **LangGraph**, **FastAPI**, **Streamlit**, and **Model Context Protocol (MCP)**. The system guides a patient through a structured intake interview, generates an AI diagnostic summary, collects physician feedback via a human-in-the-loop interrupt, and produces a downloadable PDF report.

> **Academic use only.** This system does not replace a real medical consultation.

---

## Table of Contents

- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Environment Variables](#environment-variables)
- [Running the Application](#running-the-application)
  - [Method 1 — Terminal](#method-1--terminal)
  - [Method 2 — Docker](#method-2--docker)
- [API Reference](#api-reference)
- [Workflow](#workflow)
- [Consultation Screens](#consultation-screens)

---

## Architecture

The system is composed of four independent services that communicate over HTTP:

```
┌─────────────────────────────────────────────────────────────┐
│                        User Browser                         │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Streamlit Frontend  :8501                      │
└───────────────────────────┬─────────────────────────────────┘
                            │ REST
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                FastAPI Backend  :8000                       │
└───────────────────────────┬─────────────────────────────────┘
                            │ LangGraph SDK
                            ▼
┌─────────────────────────────────────────────────────────────┐
│            LangGraph Dev Server  :2024                      │
│                                                             │
│   START → Supervisor → DiagnosticAgent ──┐                 │
│                ▲               │          │                 │
│                └───────────────┘          │                 │
│                ▲                          ▼                 │
│           PhysicianReview ◄── Supervisor ◄── ReportAgent   │
│                                   │                         │
│                                  END                        │
└───────────────────────────┬─────────────────────────────────┘
                            │ SSE / MCP
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                MCP Server  :8001                            │
│         ask_patient  │  recommend_interim_care              │
└───────────────────────────┬─────────────────────────────────┘
                            │ API call
                            ▼
                     Groq LLM  (external)
```

| Service | Port | Role |
|---|---|---|
| MCP Server | 8001 | Exposes clinical tools via Model Context Protocol |
| LangGraph | 2024 | Stateful multi-agent graph with HITL interrupt |
| FastAPI | 8000 | REST API consumed by the frontend |
| Streamlit | 8501 | 4-screen patient-facing UI with PDF export |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Agent orchestration | [LangGraph](https://github.com/langchain-ai/langgraph) 0.4+ |
| LLM provider | [Groq](https://groq.com/) — `llama-3.3-70b-versatile` |
| Tool protocol | [Model Context Protocol](https://modelcontextprotocol.io/) — FastMCP |
| REST API | [FastAPI](https://fastapi.tiangolo.com/) + Uvicorn |
| Frontend | [Streamlit](https://streamlit.io/) |
| PDF generation | [fpdf2](https://py-pdf.github.io/fpdf2/) |
| Observability | [LangSmith](https://smith.langchain.com/) |
| Containerisation | Docker + Docker Compose |

---

## Project Structure

```
medical-ai-assistant/
│
├── backend/
│   └── app/
│       ├── api.py                  # FastAPI — 5 REST endpoints
│       ├── graph.py                # LangGraph workflow compilation
│       ├── state.py                # MedicalState schema
│       ├── nodes/
│       │   ├── supervisor.py       # Routing logic
│       │   ├── diagnostic_agent.py # Patient interview + AI summary
│       │   ├── physician_agent.py  # HITL physician review (interrupt)
│       │   └── report_agent.py     # Final report generation
│       └── tools/
│           ├── mcp_client.py       # MCP SSE client (async → sync bridge)
│           ├── patient_tools.py
│           └── care_tools.py
│
├── mcp_server/
│   └── server.py                   # FastMCP — ask_patient, recommend_interim_care
│
├── frontend/
│   └── app.py                      # Streamlit UI — 4 screens
│
├── Dockerfile                      # Single image for all services
├── docker-compose.yml              # Orchestrates all 4 services
├── .env                            # Secrets (not committed)
├── .env.docker                     # Docker URL overrides (no secrets)
├── langgraph.json                  # LangGraph CLI config
└── requirements.txt                # Python dependencies
```

---

## Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.11+ |
| Docker Desktop | 4.x+ (for Docker method only) |
| Groq API key | [console.groq.com](https://console.groq.com) |
| LangSmith API key | [smith.langchain.com](https://smith.langchain.com) — optional, for tracing |

---

## Environment Variables

Create a `.env` file at the project root:

```env
# LLM
GROQ_API_KEY=gsk_...

# Observability (optional)
LANGSMITH_API_KEY=lsv2_...
LANGSMITH_TRACING=true

# Service URLs (terminal defaults — overridden by .env.docker in Docker)
LANGGRAPH_URL=http://localhost:2024
MCP_SERVER_URL=http://localhost:8001
```

> `.env` is git-ignored. Never commit API keys.

---

## Running the Application

### Method 1 — Terminal

Install dependencies once:

```bash
pip install -r requirements.txt
```

Open **4 terminals** in the project root and run one command per terminal, in order:

**Terminal 1 — MCP Server**
```bash
python mcp_server/server.py
# Listening on http://localhost:8001
```

**Terminal 2 — LangGraph**
```bash
langgraph dev
# Listening on http://localhost:2024
```

**Terminal 3 — FastAPI**
```bash
uvicorn backend.app.api:app --port 8000 --reload
# Listening on http://localhost:8000  (docs at /docs)
```

**Terminal 4 — Streamlit**
```bash
streamlit run frontend/app.py
# Listening on http://localhost:8501
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

### Method 2 — Docker

Requires Docker Desktop to be running.

**Build and start all services:**

```bash
docker compose up --build
```

**Stop all services:**

```bash
docker compose down
```

**Rebuild after a code change:**

```bash
docker compose up --build --remove-orphans
```

Open [http://localhost:8501](http://localhost:8501) once all four containers are healthy.

Services start in dependency order enforced by health checks:

```
mcp  ──►  langgraph  ──►  api  ──►  frontend
```

> **Note on fonts:** Docker uses Liberation Sans (metrically compatible with Arial) for PDF generation. Output is visually identical to the Windows terminal build.

---

## API Reference

Base URL: `http://localhost:8000`

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service liveness check |
| `POST` | `/start_session` | Create a patient session |
| `POST` | `/start_consultation` | Launch the agent graph |
| `POST` | `/consultation/resume` | Submit a patient answer or physician review |
| `GET` | `/consultation/{thread_id}` | Poll current consultation state |
| `GET` | `/consultation/{thread_id}/report` | Retrieve the final report |

Interactive Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)

### Quick example

```bash
# 1. Create a session
curl -s -X POST http://localhost:8000/start_session \
  -H "Content-Type: application/json" \
  -d '{"patient_name": "Jean Dupont"}' | jq .

# 2. Start consultation (use session_id from step 1)
curl -s -X POST http://localhost:8000/start_consultation \
  -H "Content-Type: application/json" \
  -d '{"session_id": "<session_id>", "initial_complaint": "Maux de tête sévères depuis 2 jours"}' | jq .

# 3. Submit a patient answer (use thread_id from step 2)
curl -s -X POST http://localhost:8000/consultation/resume \
  -H "Content-Type: application/json" \
  -d '{"thread_id": "<thread_id>", "patient_answer": "Depuis ce matin, intensité 7/10"}' | jq .
```

---

## Workflow

```
Patient submits name + chief complaint
            │
            ▼
      ┌─────────────┐
      │  Supervisor │  ◄─────────────────────────────────┐
      └──────┬──────┘                                     │
             │                                            │
    ┌────────▼────────┐                                   │
    │ DiagnosticAgent │                                   │
    │                 │  Calls MCP: ask_patient(0..4)     │
    │                 │  ── HITL interrupt per question ──│
    │                 │  Calls MCP: recommend_interim_care│
    │                 │  Generates AI summary via Groq    │
    └────────┬────────┘                                   │
             │                                            │
    ┌────────▼────────┐                                   │
    │ PhysicianReview │  ◄── HITL interrupt               │
    │                 │  Physician enters observations     │
    │                 │  + treatment plan                 │
    └────────┬────────┘                                   │
             │                                            │
    ┌────────▼────────┐                                   │
    │  ReportAgent    │                                   │
    │                 │  Compiles final report via Groq   │
    └────────┬────────┘                                   │
             └───────────────────────────────────────────►│
                                                    Supervisor → END
```

**MCP Tools exposed by the server:**

| Tool | Parameters | Returns |
|---|---|---|
| `ask_patient` | `question_index: int (0–4)` | One of 5 standardised clinical questions |
| `recommend_interim_care` | `symptoms_summary: str`, `severity_score: int (1–10)` | Urgency-rated care recommendations |

---

## Consultation Screens

| # | Screen | Description |
|---|---|---|
| 1 | **Saisie** | Patient enters full name and chief complaint |
| 2 | **Questions** | Patient answers 5 AI-generated clinical questions with a progress bar |
| 3 | **Médecin** | Physician reviews the AI diagnostic summary and enters clinical observations + treatment plan |
| 4 | **Rapport** | Final consultation report displayed in full with one-click PDF download |
