import type { DataQualityResponse, ApprovalStatus } from "../types"
import QualityScoreBadge from "./QualityScoreBadge"
import IssuesList from "./IssuesList"
import ApproveRejectButtons from "./ApproveRejectButtons"

interface Props {
  data: DataQualityResponse
  status: ApprovalStatus
  onApprove: () => void
  onReject: () => void
}

export default function DataQualityCard({ data, status, onApprove, onReject }: Props) {
  return (
    <div className="bg-white rounded-xl shadow p-6 flex flex-col gap-5">

      {/* Overall Score */}
      <div className="flex flex-col items-center gap-2">
        <p className="text-sm font-semibold text-gray-500">Overall Quality Score</p>
        <QualityScoreBadge score={data.overall_score} />
      </div>

      {/* Breakdown Grid */}
      <div>
        <p className="text-sm font-semibold text-gray-500 mb-3">Breakdown</p>
        <div className="flex justify-center gap-4">
          <QualityScoreBadge score={data.breakdown.completeness} label="completeness" />
          <QualityScoreBadge score={data.breakdown.accuracy} label="accuracy" />
          <QualityScoreBadge score={data.breakdown.timeliness} label="timeliness" />
          <QualityScoreBadge score={data.breakdown.clinical_plausibility} label="clinical plausibility" />
        </div>
      </div>

      {/* Issues */}
      <div>
        <p className="text-sm font-semibold text-gray-500 mb-2">Issues Detected</p>
        <IssuesList issues={data.issues_detected} />
      </div>

      {/* Approve / Reject */}
      <ApproveRejectButtons
        status={status}
        onApprove={onApprove}
        onReject={onReject}
      />

    </div>
  )
}