import axios from "axios"
import type { ReconcileRequest, ReconcileResponse, DataQualityRequest, DataQualityResponse } from "../types"

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  headers: {
    "X-API-Key": import.meta.env.VITE_API_KEY,
  },
})

export async function reconcileMedication(payload: ReconcileRequest): Promise<ReconcileResponse> {
  const { data } = await client.post<ReconcileResponse>("/api/reconcile/medication", payload)
  return data
}

export async function validateDataQuality(payload: DataQualityRequest): Promise<DataQualityResponse> {
  const { data } = await client.post<DataQualityResponse>("/api/validate/data-quality", payload)
  return data
}