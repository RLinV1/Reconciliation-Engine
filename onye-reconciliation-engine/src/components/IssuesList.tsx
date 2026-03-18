import type { DetectedIssue } from "../types"

export default function IssuesList({ issues }: { issues: DetectedIssue[] }) {
  if (issues.length === 0) {
    return <p className="text-sm text-gray-500">No issues detected.</p>
  }

  const severityStyle = (severity: DetectedIssue["severity"]) =>
    severity === "critical" ? "bg-red-100 text-red-700" :
    severity === "high"   ? "bg-red-100 text-red-700" :
    severity === "medium" ? "bg-yellow-100 text-yellow-700" :
                            "bg-blue-100 text-blue-700"

  return (
    <ul className="flex flex-col gap-2">
      {issues.map((issue, index) => (
        <li key={index} className="flex items-start justify-between gap-4 p-3 bg-gray-50 rounded-lg border border-gray-200">
          <div className="flex flex-col gap-1">
            <span className="text-xs font-mono text-gray-400">{issue.field}</span>
            <span className="text-sm text-gray-700">{issue.issue}</span>
          </div>
          <span className={`text-xs font-semibold px-2 py-1 rounded-full shrink-0 ${severityStyle(issue.severity)}`}>
            {issue.severity}
          </span>
        </li>
      ))}
    </ul>
  )
}