import type { ReconcileResponse, ApprovalStatus } from "../types";
import ConfidenceBar from "./ConfidenceBar";
import ApproveRejectButtons from "./ApproveRejectButtons";

interface Props {
  data: ReconcileResponse;
  status: ApprovalStatus;
  onApprove: () => void;
  onReject: () => void;
}

export default function ReconciliationCard({
  data,
  status,
  onApprove,
  onReject,
}: Props) {
  const safetyColor =
    data.clinical_safety_check === "PASSED"
      ? "bg-green-100 text-green-700"
      : "bg-red-100 text-red-700";

  return (
    <div className="bg-white rounded-xl shadow p-6 flex flex-col gap-5">

      {/* Medication Name + Safety Badge */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-800">
          {data.reconciled_medication}
        </h2>
        <span className={`text-xs font-semibold px-3 py-1 rounded-full ${safetyColor}`}>
          {data.clinical_safety_check}
        </span>
      </div>

      {/* Confidence Bar */}
      <ConfidenceBar score={data.confidence_score} />

      {/* Reasoning */}
      <div>
        <p className="text-sm font-semibold text-gray-500 mb-1">Reasoning</p>
        <p className="text-sm text-gray-700 bg-gray-50 rounded-lg p-3 border border-gray-200">
          {data.reasoning}
        </p>
      </div>

      {/* Recommended Actions */}
      <div>
        <p className="text-sm font-semibold text-gray-500 mb-1">
          Recommended Actions
        </p>
        <ul className="flex flex-col gap-1">
          {data.recommended_actions.map((action, index) => (
            <li key={index} className="text-sm text-gray-700 flex items-start gap-2">
              <span className="text-blue-500 mt-0.5">→</span>
              {action}
            </li>
          ))}
        </ul>
      </div>

      {/* Approve / Reject */}
      <ApproveRejectButtons
        status={status}
        onApprove={onApprove}
        onReject={onReject}
      />

    </div>
  );
}