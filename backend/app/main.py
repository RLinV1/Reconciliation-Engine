from fastapi import FastAPI, Security, HTTPException
from fastapi.security.api_key import APIKeyHeader
from ollama import chat, Client
from app.core.cache import cache
from dotenv import load_dotenv
from app.models.medication import ReconcileRequest, ReconcileResponse, DataQualityRequest, DataQualityResponse
import json
import os
from fastapi.middleware.cors import CORSMiddleware
import re

load_dotenv()

app = FastAPI(title="EHR Reconciliation Engine")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = os.getenv("API_KEY")
OLLAMA_HOST = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
ollama_client = Client(host=OLLAMA_HOST)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def fix_truncated_json(text: str) -> str:
    text = text.strip()
    # strip markdown fences
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    text = text.strip()
    # if missing closing brace, add it
    open_braces = text.count("{")
    close_braces = text.count("}")
    if open_braces > close_braces:
        text += "}" * (open_braces - close_braces)
    return text

def verify_api_key(api_key: str = Security(api_key_header)):
    if not api_key:
        raise HTTPException(status_code=403, detail="Missing API key")
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key

@app.get("/api/health")
def health():
    return {"status": "healthy"}

@app.post("/api/reconcile/medication", response_model=ReconcileResponse)
def reconcile_medication(request: ReconcileRequest, api_key: str = Security(verify_api_key)):
    
    request_dict = request.model_dump(exclude={"invalidate_cache"})
    
    if request.invalidate_cache:
        cache.delete(request_dict)
        print(f"Cache invalidated due to rejection")

    cached = cache.get(request_dict)
    if cached:
        print("Cache hit!")
        return ReconcileResponse(**cached)
    
    sources_text = "\n".join([
        f"- {s.system}: {s.medication} (updated: {s.last_updated or s.last_filled}, reliability: {s.source_reliability})"
        for s in request.sources
    ])

    context_text = ""
    if request.patient_context:
        ctx = request.patient_context
        context_text = f"""
            Patient context:
            - Age: {ctx.age}
            - Conditions: {', '.join(ctx.conditions)}
            - Labs: {ctx.recent_labs}
        """

    prompt = f"""You are a clinical pharmacist reconciling conflicting medication records.

        Conflicting sources:
        {sources_text}

        Patient context:
        {context_text}

        Rules for reconciliation:
        1. The most RECENT record from a HIGH reliability source is preferred.
        2. Patient clinical context (labs, conditions) MUST override source reliability.
        - If eGFR < 45, Metformin dose should be reduced or stopped entirely.
        - If eGFR 45-60, Metformin dose should not exceed 500mg twice daily.
        - If eGFR > 60, standard dosing applies.
        3. A more recent LOW reliability source can override an older HIGH reliability source.
        4. Pharmacy fills reflect what was PREVIOUSLY prescribed, not the current recommendation.
        5. If clinical labs suggest a dose is unsafe, flag it even if the source is reliable.

        Based on the above rules, determine the most clinically appropriate medication and dose.

        Respond ONLY with this exact JSON, nothing else:
        {{
            "reconciled_medication": "string - the correct medication name and dose",
            "confidence_score": 0.0 to 1.0,
            "reasoning": "string - explain why this is the correct medication referencing patient labs and conditions",
            "recommended_actions": [
                "Update [outdated system] from [wrong dose] to [correct dose]",
                "Verify with pharmacist that [correct dose] is being filled"
            ],
            "clinical_safety_check": "PASSED or WARNING or FAILED"
        }}

        Do NOT return any text outside the JSON. Do NOT use markdown. Return raw JSON only.
    """

    response = ollama_client.chat(
        model='llama3.2',
        messages=[
            {
                'role': 'system',
                'content': 'You are a clinical pharmacist. You only respond in valid JSON. Never add text outside the JSON.'
            },
            {
                'role': 'user',
                'content': prompt
            }
        ],
        options={
            'num_predict': 1000,
            'temperature': 0.1,
        }
    )

    try:
        raw = response.message.content
        cleaned = fix_truncated_json(raw)
        data = json.loads(cleaned)
        print(data)
        cache.set(request_dict, data)
        return ReconcileResponse(**data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="AI returned invalid JSON")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Response validation failed: {str(e)}")


@app.post("/api/validate/data-quality", response_model=DataQualityResponse)
def validate_data_quality(request: DataQualityRequest, api_key: str = Security(verify_api_key)):
    request_dict = request.model_dump(exclude={"invalidate_cache"})
    
    if request.invalidate_cache:
        cache.delete(request_dict)
        print(f"Cache invalidated due to rejection")

    cached = cache.get(request_dict)
    if cached:
        print("Cache hit!")
        return DataQualityResponse(**cached)
    

    demographics = request.demographics.model_dump() if request.demographics else {}
    vital_signs = request.vital_signs.model_dump() if request.vital_signs else {}

    # pre-parse blood pressure before sending to LLM
    systolic = None
    bp = vital_signs.get("blood_pressure", "")
    if isinstance(bp, str) and "/" in bp:
        try:
            systolic = int(bp.split("/")[0])
        except ValueError:
            pass

    bp_note = ""
    if systolic is not None:
        if systolic > 280:
            bp_note = f"CRITICAL: Systolic BP is {systolic} which is physiologically impossible."
        elif systolic > 180:
            bp_note = f"HIGH: Systolic BP is {systolic} which is dangerously elevated."

    prompt = f"""You are a clinical data quality analyst. Analyze this patient record and score it.

    Demographics: {json.dumps(demographics)}
    Medications: {json.dumps(request.medications)}
    Allergies: {json.dumps(request.allergies)}
    Conditions: {json.dumps(request.conditions)}
    Vital Signs: {json.dumps(vital_signs)}
    Last Updated: {request.last_updated}

    Pre-analyzed findings (you MUST include these in issues_detected):
    - Blood pressure: {bp_note if bp_note else "within normal range"}
    - Allergies: {"EMPTY - flag as medium severity issue" if not request.allergies else "has entries"}
    - Last updated: {request.last_updated} — {"flag as medium timeliness issue, data is stale" if request.last_updated < "2024-09-18" else "recent enough"}

    Current field status:
    - name: {"PRESENT" if demographics.get("name") else "MISSING"}
    - dob: {"PRESENT" if demographics.get("dob") else "MISSING"}
    - gender: {"PRESENT" if demographics.get("gender") else "MISSING"}
    - allergies: {"PRESENT - has entries" if request.allergies else "MISSING or EMPTY"}
    - medications: {"PRESENT" if request.medications else "MISSING"}
    - conditions: {"PRESENT" if request.conditions else "MISSING"}
    - vital_signs: {"PRESENT" if vital_signs else "MISSING"}
    - last_updated: {"PRESENT" if request.last_updated else "MISSING"}

    Scoring rules — start every score at 100 and deduct:
    - Each MISSING required field: -10 from completeness
    - Each medium severity issue: -10 from overall and relevant breakdown score
    - Each high severity issue: -20 from overall and relevant breakdown score
    - Each critical severity issue: -30 from overall and clinical_plausibility
    - Data older than 6 months: -10 from timeliness
    - Data older than 12 months: -20 from timeliness

    Breakdown score meanings:
    - completeness: are all required fields present and filled? (name, dob, gender, medications, conditions, vital_signs, last_updated, allergies)
    - accuracy: are the values correct and not contradictory?
    - timeliness: how recent is the data?
    - clinical_plausibility: are the clinical values physiologically possible?

    A record with a high severity issue should score below 70.
    A record with a critical severity issue should NEVER score above 50.

    Example input/output for reference:
    Input: allergies=[], blood_pressure="340/180", last_updated="2024-06-15"
    Output scores: overall=62, completeness=60, accuracy=50, timeliness=70, clinical_plausibility=40
    Issues: allergies(medium), vital_signs.blood_pressure(high), last_updated(medium)

    Respond ONLY with this exact JSON, nothing else:
    {{
        "overall_score": 0 to 100,
        "breakdown": {{
            "completeness": 0 to 100,
            "accuracy": 0 to 100,
            "timeliness": 0 to 100,
            "clinical_plausibility": 0 to 100
        }},
        "issues_detected": [
            {{
                "field": "field name",
                "issue": "description of issue",
                "severity": "low or medium or high or critical"
            }}
        ]
    }}

    Do NOT return any text outside the JSON. Do NOT use markdown. Return raw JSON only."""

    response = ollama_client.chat(
        model='llama3.2',
        messages=[
            {
                'role': 'system',
                'content': 'You are a clinical data quality analyst. You only respond in valid JSON. Never add text outside the JSON.'
            },
            {
                'role': 'user',
                'content': prompt
            }
        ],
        options={
            'num_predict': 1000,
            'temperature': 0.1,
        }
    )

    try:
        raw = response.message.content
        cleaned = fix_truncated_json(raw)
        data = json.loads(cleaned)
        cache.set(request_dict, data)
        return DataQualityResponse(**data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="AI returned invalid JSON")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Response validation failed: {str(e)}")