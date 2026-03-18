# Clinical Data Reconciliation Engine

A full-stack application that uses AI to reconcile conflicting patient medication records across multiple healthcare systems and validate patient data quality.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Running Locally (Without Docker)](#running-locally-without-docker)
- [Running Locally (With Docker Desktop)](#running-locally-with-docker-desktop)
- [API Endpoints](#api-endpoints)
- [LLM Choice & Reasoning](#llm-choice--reasoning)
- [Key Design Decisions & Trade-offs](#key-design-decisions--trade-offs)
- [What I'd Improve With More Time](#what-id-improve-with-more-time)
- [Estimated Time Spent](#estimated-time-spent)


## Overview

Healthcare providers often store conflicting information about the same patient across different systems. This engine uses AI (Llama 3.2 via Ollama) to:

- **Reconcile** conflicting medication records from multiple sources into a single truth with a confidence level
- **Validate** Validate patient data quality across dimensions like completeness, accuracy, timeliness, and plausability


The frontend is deployed on Vercel for live preview: https://reconciliation-engine-jade.vercel.app/

The backend is not publicly hosted due to the computational requirements of running a local LLM (Llama 3.2 via Ollama), which requires dedicated hardware resources that fall outside the scope of this assessment. To fully experience the application with live AI responses, the backend must be run locally by following the setup instructions below.

---

## Tech Stack

| Layer    | Technology          |
|----------|---------------------|
| Backend  | Python + FastAPI     |
| AI/LLM   | Llama 3.2 (via Ollama) |
| Frontend | React (Vite)         |
| Database | In-memory (no DB required) |
| Containerization | Docker + Docker Compose |

---

## Running Locally (Without Docker)

### Prerequisites

- Python 3.10+
- Node.js 18+
- [Ollama](https://ollama.com) installed and running

> MAKE SURE THAT THE VITE_API_KEY and backend API_KEY are the same

### 1. Pull the LLM model

```bash
ollama pull llama3.2
```

Make sure Ollama is running in the background:

```bash
ollama serve
```

### 2. Clone the repository

```bash
git clone https://github.com/RLinV1/Reconciliation-Engine.git
cd Reconciliation-Engine
```

### 3. Set up the backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the `/backend` directory:

```env
API_KEY=your-secret-api-key-here
OLLAMA_BASE_URL=http://localhost:11434 
```

Start the backend server:

```bash
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`  
Docs at `http://localhost:8000/docs`

### 4. Set up the frontend

```bash
cd ../frontend
npm install
```

Create a `.env` file in the `/frontend` directory:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_API_KEY=your-secret-api-key-here
```

Start the frontend:

```bash
npm run dev
```

The app will be available at `http://localhost:5173`

### 5. Run the tests

```bash
cd backend
pytest tests/ -v
```

---

## Running Locally (With Docker Desktop)

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- [Ollama](https://ollama.com) installed on your host machine

> MAKE SURE THAT THE VITE_API_KEY and backend API_KEY are the same

### 1. Pull the LLM model (on host machine)

> Currently the Ollama is ran through docker desktop but this require at least 6 GB of RAM dedicated to your containers. You can also serve the ollama model on your computer without docker containers. This requires changing up the code 


```bash
ollama pull llama3.2
ollama serve
```


> Ollama runs on the host, not inside Docker, to avoid downloading the model inside the container.


### 2. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/ehr-reconciliation-engine.git
cd ehr-reconciliation-engine
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
API_KEY=your-secret-api-key-here
OLLAMA_BASE_URL=http://ollama:11434
VITE_API_BASE_URL=http://localhost:8000
VITE_API_KEY=your-secret-api-key-here
```

### 4. Build and run with Docker Compose

```bash
docker compose up --build
```

| Service  | URL                        |
|----------|----------------------------|
| Frontend | http://localhost:5173       |
| Backend  | http://localhost:8000       |
| API Docs | http://localhost:8000/docs  |

### 5. Stop the containers

```bash
docker compose down
```

---

## API Endpoints

All endpoints require the header: `X-API-Key: your-secret-api-key-here`

### `POST /api/reconcile/medication`

Reconciles conflicting medication records from multiple sources.

**Request body:**
```json
{
  "patient_context": {
    "age": 67,
    "conditions": ["Type 2 Diabetes", "Hypertension"],
    "recent_labs": { "eGFR": 45 }
  },
  "sources": [
    {
      "system": "Hospital EHR",
      "medication": "Metformin 1000mg twice daily",
      "last_updated": "2024-10-15",
      "source_reliability": "high"
    },
    {
      "system": "Primary Care",
      "medication": "Metformin 500mg twice daily",
      "last_updated": "2025-01-20",
      "source_reliability": "high"
    }
  ]
}
```

**Response:**
```json
{
    "reconciled_medication": "Metformin 500mg twice daily",
    "confidence_score": 0.88,
    "reasoning": "Primary care record is most recent clinical encounter. Dose reduction
    appropriate given declining kidney function (eGFR 45). Pharmacy fill may reflect old
    prescription.",
    "recommended_actions": [
        "Update Hospital EHR to 500mg twice daily",
        "Verify with pharmacist that correct dose is being filled"
    ],
    "clinical_safety_check": "PASSED"
}
```

---

### `POST /api/validate/data-quality`

Validates a patient record and scores its data quality.

**Request body:**
```json
{
  "demographics": { "name": "John Doe", "dob": "1955-03-15", "gender": "M" },
  "medications": ["Metformin 500mg", "Lisinopril 10mg"],
  "allergies": [],
  "conditions": ["Type 2 Diabetes"],
  "vital_signs": { "blood_pressure": "340/180", "heart_rate": 72 },
  "last_updated": "2024-06-15"
}
```

**Response:**
```json
{
  "overall_score": 62,
  "breakdown": {
    "completeness": 60,
    "accuracy": 50,
    "timeliness": 70,
    "clinical_plausibility": 40
  },
  "issues_detected": [
    {
        "field": "allergies",
        "issue": "No allergies documented - likely incomplete",
        "severity": "medium"
    },
    {
        "field": "vital_signs.blood_pressure",
        "issue": "Blood pressure 340/180 is physiologically implausible",
        "severity": "high"
    },
    {
        "field": "last_updated",
        "issue": "Data is 7+ months old",
        "severity": "medium"
    }
]
}
```

---

## LLM Choice & Reasoning

**Model: Llama 3.2 via [Ollama](https://ollama.com)**

I chose Llama 3.2 running locally via Ollama for the following reasons:

- **Cost**: Completely free — no API costs or usage limits
- **Speed**: Llama 3.2 (3B parameter version) is fast on consumer hardware
- **Privacy**: Patient data never leaves the local machine, which is important in a healthcare context
- **Offline capability**: Works without an internet connection once the model is downloaded

**Trade-off:** The reasoning quality is not as strong as GPT-4 or Claude Sonnet. With a real production budget, I would switch to 

**Anthropic Claude** (claude-sonnet) for its superior clinical reasoning and more reliable structured JSON output. Claude also has better instruction-following, which matters when prompting for specific output formats. 

**Meditron** is trained on medical data but it didn't follow instructions when prompted and oftentimes led to more errors than being helpful

---

## Key Design Decisions & Trade-offs

### 1. FastAPI over Flask or Node.js
FastAPI was chosen for its automatic documentation, native async support (important for LLM calls), and Pydantic-based request validation. It was picked due to performance and the ability to test endpoints easily through the web. The trade-off is a slightly steeper learning curve than Flask.

### 2. In-memory caching for LLM responses
Identical requests are cached in a Python dictionary to avoid redundant LLM calls. This is fast and simple, but is wiped on server restart. A production system would use Redis.

### 4. Source reliability weighting
The reconciliation logic weights source records by both `source_reliability` (high/medium/low) and recency (`last_updated`). This means a recent "high" reliability source beats an older "high" source — which reflects real-world clinical practice.

### 5. API key authentication
A simple `X-API-Key` header guard protects all endpoints. This is intentionally lightweight for a take-home project. In production, this would be replaced with OAuth2 / JWT.

### 6. No database
All state is in-memory through a cache. This keeps setup friction to zero. The trade-off is no persistence across restarts and no audit logging of reconciliation decisions.

---

## What I'd Improve With More Time

- **Switch to Claude Sonnet or GPT-4** for significantly better clinical reasoning quality
- **Add Redis** for persistent caching and session management
- **Persist reconciliation history** in a PostgreSQL database or MongoDB database
- **Confidence score calibration** using a weighted multi-factor model to determine confidence
- **Duplicate record detection** utilize hashing to make sure records aren't duplicated
- **Better frontend UX** — currently focused on functionality. Later on I would make it more accessible to more audiences and add filtering, sorting, and a reconciliation history view
- **More comprehensive test coverage** — currently 5+ unit tests; would add integration tests and mock LLM responses for CI

---

## Estimated Time Spent

| Task                              | Time     |
|-----------------------------------|----------|
| Reading requirements & planning   | 1 hr   |
| Backend API + validation logic    | 3 hrs    |
| LLM prompt engineering + integration | 2 hrs |
| Frontend dashboard                | 2 hrs    |
| Docker setup                      | 45 min   |
| Tests                             | 45 min   |
| README + documentation            | 30 min   |
| **Total**                         | **~10 hrs** |

---





