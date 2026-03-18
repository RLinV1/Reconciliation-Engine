interface Props {
  score: number; // 0 to 1
}

export default function ConfidenceBar({ score }: Props) {
  const percentage = Math.round(score * 100);

  const color =
    score >= 0.75
      ? "bg-green-500"
      : score >= 0.5
        ? "bg-yellow-500"
        : "bg-red-500";

  const textColor =
    score >= 0.75
      ? "text-green-500"
      : score >= 0.5
        ? "text-yellow-500"
        : "text-red-500";

  return (
    <div className="w-full">
      <div className="flex justify-between mb-1">
        <span className="text-sm text-gray-500">Confidence Score</span>
        <span className={`text-sm font-bold ${textColor}`}>{percentage}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2.5">
        <div
          className={`${color} h-2.5 rounded-full transition-all duration-500`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
