import { useState } from "react";
import type { DataQualityResponse, ApprovalStatus } from "../types";
import { validateDataQuality } from "../services/api";
import DataQualityCard from "../components/DataQualityCard";
import { QUALITY_SCENARIOS as MOCK_SCENARIOS } from "../data/data";
import Spinner from "../components/Spinner";
import axios from "axios";

export default function QualityPage() {
  const [selectedScenario, setSelectedScenario] = useState<string>("");
  const [input, setInput] = useState<string>("");
  const [result, setResult] = useState<DataQualityResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [approval, setApproval] = useState<ApprovalStatus>("pending");

  const handleApprove = () => {
    setApproval("approved");
  };

  const handleReject = async () => {
    setApproval("rejected");
    try {
      await validateDataQuality({
        ...JSON.parse(input),
        invalidate_cache: true,
        decision: "rejected",
      });
    } catch (err) {
      console.log("Cache invalidation failed", err);
    }
  };

  const handleScenarioChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const name = e.target.value;
    setSelectedScenario(name);
    if (name) {
      setInput(JSON.stringify(MOCK_SCENARIOS[name], null, 2));
    } else {
      setInput("");
    }
    setResult(null);
    setError(null);
    setApproval("pending");
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
      const text = event.target?.result as string;
      setInput(text);
      setSelectedScenario("");
      setResult(null);
      setError(null);
      setApproval("pending");
    };
    reader.readAsText(file);
  };

  const handleSubmit = async () => {
    setError(null);
    setResult(null);
    setApproval("pending");
    setLoading(true);

    try {
      const parsed = JSON.parse(input);
      const data = await validateDataQuality(parsed);
      setResult(data);
    } catch (err) {
      console.log(err);
      if (err instanceof SyntaxError) {
        setError("Invalid JSON — please check your input.");
      } else if (axios.isAxiosError(err)) {
        const detail = err.response?.data?.detail;
        setError(detail ?? "Something went wrong. Is the backend running?");
      } else {
        setError("Something went wrong. Is the backend running?");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-5">
      <div className="bg-white rounded-xl shadow p-6 flex flex-col gap-3">

        <div className="flex items-center justify-between">
          <p className="text-sm font-semibold text-gray-500">
            Paste your patient record or load one of the example scenarios
          </p>
          <div className="flex items-center gap-2">
            <select
              value={selectedScenario}
              onChange={handleScenarioChange}
              className="text-xs border border-gray-300 rounded-lg px-2 py-1 bg-gray-50 text-gray-600 focus:outline-none"
            >
              <option value="">— Load example —</option>
              {Object.keys(MOCK_SCENARIOS).map((name) => (
                <option key={name} value={name}>
                  {name}
                </option>
              ))}
            </select>
            <label className="cursor-pointer text-xs px-3 py-1 bg-gray-100 hover:bg-gray-200 text-gray-600 rounded-lg border border-gray-300 transition-colors">
              Upload JSON
              <input
                type="file"
                accept=".json"
                onChange={handleFileUpload}
                className="hidden"
              />
            </label>
          </div>
        </div>

        <textarea
          value={input}
          onChange={(e) => {
            setInput(e.target.value);
            setSelectedScenario("");
          }}
          rows={14}
          placeholder={`Paste your JSON here, for example:\n{\n  "demographics": { ... },\n  "medications": [ ... ],\n  "allergies": [...],\n  "conditions": [...],\n  "vital_signs": {...},\n  "last_updated": "..."\n}`}
          className="w-full text-sm font-mono bg-gray-50 border border-gray-200 rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-blue-300"
        />

        <button
          onClick={handleSubmit}
          disabled={loading || !input.trim()}
          className="self-end px-6 py-2 cursor-pointer bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-semibold rounded-lg transition-colors"
        >
          {loading ? "Analyzing..." : "Validate"}
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg p-3">
          {error}
        </div>
      )}

      {loading && <Spinner />}
      {!loading && result && (
        <DataQualityCard
          data={result}
          status={approval}
          onApprove={handleApprove}
          onReject={handleReject}
        />
      )}
    </div>
  );
}