interface Props {
  score: number // 0 to 100
  label?: string
}

export default function QualityScoreBadge({ score, label }: Props) {
  const color =
    score >= 75 ? "bg-green-100 text-green-700 border-green-300" :
    score >= 50 ? "bg-yellow-100 text-yellow-700 border-yellow-300" :
                  "bg-red-100 text-red-700 border-red-300"

  const ringColor =
    score >= 75 ? "text-green-500" :
    score >= 50 ? "text-yellow-500" :
                  "text-red-500"

  return (
    <div className="flex flex-col items-center gap-1">
      <div className={`w-24 h-24 rounded-full border-4 flex items-center justify-center font-bold text-xl ${color} ${ringColor}`}>
        {score}
      </div>
      {label && (
        <span className="text-xs text-gray-500 text-center capitalize">{label}</span>
      )}
    </div>
  )
}