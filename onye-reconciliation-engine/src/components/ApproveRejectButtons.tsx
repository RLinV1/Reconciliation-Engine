import type { ApprovalStatus } from "../types"

interface Props {
  status: ApprovalStatus
  onApprove: () => void
  onReject: () => void
}

export default function ApproveRejectButtons({ status, onApprove, onReject }: Props) {
  if (status === "approved") {
    return <p className="text-sm font-semibold text-green-600">✓ Suggestion Approved</p>
  }

  if (status === "rejected") {
    return <p className="text-sm font-semibold text-red-600">✗ Suggestion Rejected</p>
  }

  return (
    <div className="flex gap-3">
      <button
        onClick={onApprove}
        className="cursor-pointer flex-1 py-2 px-4 bg-green-500 hover:bg-green-600 text-white text-sm font-semibold rounded-lg transition-colors"
      >
        ✓ Approve
      </button>
      <button
        onClick={onReject}
        className="cursor-pointer flex-1 py-2 px-4 bg-red-500 hover:bg-red-600 text-white text-sm font-semibold rounded-lg transition-colors"
      >
        ✗ Reject
      </button>
    </div>
  )
}