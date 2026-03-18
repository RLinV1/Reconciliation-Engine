import { useState } from "react"
import ReconcilePage from "./pages/ReconcilePage"
import QualityPage from "./pages/QualityPage"

type Tab = "reconcile" | "quality"

export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>("reconcile")

  return (
    <div className="min-h-screen bg-gray-100">

      <div className="w-full bg-white shadow">
        <div className="flex flex-col justify-center items-center px-4 py-4">
          <h1 className="text-4xl font-bold text-gray-800">Clinical Data Reconciliation Engine</h1>
          <p className="text-sm text-gray-500">AI-powered EHR data reconciliation and quality validation</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-3xl mx-auto px-4 flex gap-6">
          <button
            onClick={() => setActiveTab("reconcile")}
            className={`py-3 cursor-pointer text-md font-semibold border-b-2 transition-colors ${
              activeTab === "reconcile"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            Medication Reconciliation
          </button>
          <button
            onClick={() => setActiveTab("quality")}
            className={`py-3 cursor-pointer text-md font-semibold border-b-2 transition-colors ${
              activeTab === "quality"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            Data Quality Validator
          </button>
        </div>
      </div>

      {/* Page Content */}
      <div className="max-w-3xl mx-auto px-4 py-6">
        {activeTab === "reconcile" ? <ReconcilePage /> : <QualityPage />}
      </div>

    </div>
  )
}