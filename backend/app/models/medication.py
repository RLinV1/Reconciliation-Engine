from pydantic import BaseModel
from typing import Optional, List

# --- Reconcile Models ---
class MedicationSource(BaseModel):
    system: str
    medication: str
    last_updated: Optional[str] = None
    last_filled: Optional[str] = None
    source_reliability: str = "medium"

class PatientContext(BaseModel):
    age: Optional[int] = None
    conditions: Optional[List[str]] = []
    recent_labs: Optional[dict] = {}

class ReconcileRequest(BaseModel):
    patient_context: Optional[PatientContext] = None
    sources: List[MedicationSource]
    invalidate_cache: Optional[bool] = False

class ReconcileResponse(BaseModel):
    reconciled_medication: str
    confidence_score: float
    reasoning: str
    recommended_actions: List[str]
    clinical_safety_check: str

# --- Data Quality Models ---
class VitalSigns(BaseModel):
    blood_pressure: Optional[str] = None
    heart_rate: Optional[float] = None

class Demographics(BaseModel):
    name: Optional[str] = None
    dob: Optional[str] = None
    gender: Optional[str] = None

class DataQualityRequest(BaseModel):
    demographics: Optional[Demographics] = None
    medications: Optional[List[str]] = []
    allergies: Optional[List[str]] = []
    conditions: Optional[List[str]] = []
    vital_signs: Optional[VitalSigns] = None
    last_updated: Optional[str] = None
    invalidate_cache: Optional[bool] = False


class QualityIssue(BaseModel):
    field: str
    issue: str
    severity: str

class DataQualityResponse(BaseModel):
    overall_score: int
    breakdown: dict
    issues_detected: List[QualityIssue]
