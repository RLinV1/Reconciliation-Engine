export const RECONCILE_SCENARIOS: Record<string, object> = {
  "Metformin Conflict": {
    patient_context: {
      age: 67,
      conditions: ["Type 2 Diabetes", "Hypertension"],
      recent_labs: { eGFR: 45 }
    },
    sources: [
      { system: "Hospital EHR", medication: "Metformin 1000mg twice daily", last_updated: "2024-10-15", source_reliability: "high" },
      { system: "Primary Care", medication: "Metformin 500mg twice daily", last_updated: "2025-01-20", source_reliability: "high" },
      { system: "Pharmacy", medication: "Metformin 1000mg daily", last_filled: "2025-01-25", source_reliability: "medium" }
    ]
  },
  "Aspirin Conflict": {
    patient_context: {
      age: 55,
      conditions: ["Hypertension"],
      recent_labs: {}
    },
    sources: [
      { system: "Hospital EHR", medication: "Aspirin 81mg daily", last_updated: "2024-08-10", source_reliability: "high" },
      { system: "Clinic System B", medication: "Aspirin 325mg daily", last_updated: "2024-09-01", source_reliability: "high" },
      { system: "Pharmacy", medication: "Aspirin 81mg", last_filled: "2025-01-15", source_reliability: "medium" },
      { system: "Patient Portal", medication: "Not currently taking aspirin", last_updated: "2025-01-20", source_reliability: "low" }
    ]
  },
  "Lisinopril Conflict": {
    patient_context: {
      age: 72,
      conditions: ["Heart Failure", "Hypertension"],
      recent_labs: { eGFR: 60, potassium: 5.1 }
    },
    sources: [
      { system: "Cardiologist", medication: "Lisinopril 20mg daily", last_updated: "2025-01-10", source_reliability: "high" },
      { system: "Primary Care", medication: "Lisinopril 10mg daily", last_updated: "2024-11-05", source_reliability: "high" },
      { system: "Pharmacy", medication: "Lisinopril 10mg daily", last_filled: "2025-01-18", source_reliability: "medium" }
    ]
  }
}

export const QUALITY_SCENARIOS: Record<string, object> = {
  "Implausible Vitals": {
    demographics: { name: "John Doe", dob: "1955-03-15", gender: "M" },
    medications: ["Metformin 500mg", "Lisinopril 10mg"],
    allergies: [],
    conditions: ["Type 2 Diabetes"],
    vital_signs: { blood_pressure: "340/180", heart_rate: 72 },
    last_updated: "2024-06-15"
  },
  "Complete Record": {
    demographics: { name: "Jane Smith", dob: "1970-08-22", gender: "F" },
    medications: ["Atorvastatin 20mg", "Metoprolol 50mg"],
    allergies: ["Penicillin"],
    conditions: ["Hypertension", "High Cholesterol"],
    vital_signs: { blood_pressure: "128/82", heart_rate: 68 },
    last_updated: "2025-01-20"
  },
  "Missing Data": {
    demographics: { name: "Bob Jones", dob: "", gender: "" },
    medications: [],
    allergies: [],
    conditions: [],
    vital_signs: {},
    last_updated: "2023-01-01"
  }
}