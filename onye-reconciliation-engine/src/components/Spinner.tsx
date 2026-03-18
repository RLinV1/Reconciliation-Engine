import { useEffect, useState } from "react";

export default function Spinner() {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 95) {
          clearInterval(interval);
          return prev;
        }
        const increment =
          prev < 30 ? 1.5 : prev < 60 ? 1 : prev < 80 ? 0.5 : 0.2;
        return Math.min(prev + increment, 95);
      });
    }, 200);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex flex-col gap-3 py-2 px-4">
      <div className="flex justify-between text-sm">
        <span className="text-gray-500">Analyzing...</span>
        <span className="font-semibold text-blue-600">
          {Math.round(progress)}%
        </span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2.5">
        <div
          className="bg-blue-600 h-2.5 rounded-full transition-all duration-200"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}
