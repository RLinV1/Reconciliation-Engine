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
    
    prompt = f"""You are a clinical data quality analyst. Analyze this patient record and return a quality score as JSON.

        Demographics: {json.dumps(demographics)}
        Medications: {json.dumps(request.medications)}
        Allergies: {json.dumps(request.allergies)}
        Conditions: {json.dumps(request.conditions)}
        Vital Signs: {json.dumps(vital_signs)}
        Last Updated: {request.last_updated}

        ---
        PRE-ANALYZED FINDINGS — treat these as confirmed facts, include all of them in issues_detected:
        - Blood pressure: {bp_note if bp_note else "within normal range"}
        - Allergies: {"EMPTY - flag as medium severity issue" if not request.allergies else "has entries"}
        - Last updated: {request.last_updated} — {"flag as medium timeliness issue, data is stale" if request.last_updated < "2024-09-18" else "recent enough"}

        FIELD PRESENCE:
        - name: {"PRESENT" if demographics.get("name") else "MISSING"}
        - dob: {"PRESENT" if demographics.get("dob") else "MISSING"}
        - gender: {"PRESENT" if demographics.get("gender") else "MISSING"}
        - allergies: {"PRESENT - has entries" if request.allergies else "MISSING or EMPTY"}
        - medications: {"PRESENT" if request.medications else "MISSING"}
        - conditions: {"PRESENT" if request.conditions else "MISSING"}
        - vital_signs: {"PRESENT" if vital_signs else "MISSING"}
        - last_updated: {"PRESENT" if request.last_updated else "MISSING"}

        ---
        STEP-BY-STEP SCORING INSTRUCTIONS — follow exactly in this order:

        STEP 1 — Score each breakdown dimension starting at 100:

        COMPLETENESS (start at 100):
        - Deduct 30 for each MISSING required field (name, dob, gender, allergies, medications, conditions, vital_signs, last_updated)
        - Deduct 10 for each EMPTY required field (present but no value, e.g. allergies list is empty)
        - Floor at 0.

        ACCURACY (start at 100):
        - Deduct 20 for each medium-severity data contradiction
        - Deduct 30 for each high-severity contradiction
        - Deduct 40 for each critical clinical implausibility (e.g. systolic BP of 300+, heart rate of 0, impossible lab values)
        - Floor at 0.

        TIMELINESS (start at 100):
        - Deduct 10 if data is 6–12 months old
        - Deduct 20 if data is older than 12 months
        - Floor at 0.

        CLINICAL_PLAUSIBILITY (start at 100):
        - Deduct 10 for each medium-severity clinical issue
        - Deduct 20 for each high-severity clinical issue
        - Deduct 40 for each critical clinical issue (e.g. physiologically impossible vital sign)
        - Floor at 0.

        STEP 2 — Compute raw overall score:
        overall = average of (completeness + accuracy + timeliness + clinical_plausibility)

        STEP 3 — Apply issue-severity caps. These are HARD CEILINGS and override the calculated score:
        - If ANY critical issue exists → overall_score MUST be 40 or below. No exceptions.
        - If ANY high issue exists (and no critical) → overall_score MUST be 69 or below.
        - If ONLY medium/low issues exist → overall_score may be up to 85.

        STEP 4 — Apply the same caps to breakdown scores:
        - clinical_plausibility MUST be 40 or below if a critical clinical issue exists.
        - accuracy MUST be 40 or below if a critical accuracy/plausibility issue exists.

        ---
        OUTPUT FORMAT — respond ONLY with this exact JSON, no markdown, no extra text:
        {{
            "overall_score": <integer 0-100>,
            "breakdown": {{
                "completeness": <integer 0-100>,
                "accuracy": <integer 0-100>,
                "timeliness": <integer 0-100>,
                "clinical_plausibility": <integer 0-100>
            }},
            "issues_detected": [
                {{
                    "field": "<field name>",
                    "issue": "<description>",
                    "severity": "<low|medium|high|critical>"
                }}
            ]
        }}
    """

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