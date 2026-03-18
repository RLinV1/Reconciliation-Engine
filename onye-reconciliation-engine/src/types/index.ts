export interface MedicationSource {
  system: string
  medication: string
  last_updated?: string
  last_filled?: string
  source_reliability: "high" | "medium" | "low"
}

export interface PatientContext {
  age: number
  conditions: string[]
  recent_labs?: Record<string, number>
}

export interface ReconcileRequest {
  patient_context: PatientContext
  sources: MedicationSource[]
}

export interface ReconcileResponse {
  reconciled_medication: string
  confidence_score: number
  reasoning: string
  recommended_actions: string[]
  clinical_safety_check: "PASSED" | "FAILED"
}

export interface QualityBreakdown {
  completeness: number
  accuracy: number
  timeliness: number
  clinical_plausibility: number
}

export interface DetectedIssue {
  field: string
  issue: string
  severity: "critical" | "high" | "medium" | "low"
}

export interface DataQualityRequest {
  demographics: {
    name: string
    dob: string
    gender: string
  }
  medications: string[]
  allergies: string[]
  conditions: string[]
  vital_signs: Record<string, string | number>
  last_updated: string
}

export interface DataQualityResponse {
  overall_score: number
  breakdown: QualityBreakdown
  issues_detected: DetectedIssue[]
}

export type ApprovalStatus = "pending" | "approved" | "rejected"