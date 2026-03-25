import { useState, useEffect } from "react";

interface StaleIndicatorProps {
  fetchedAt: string | null | undefined;
  thresholdMinutes?: number;
}

const STYLE: React.CSSProperties = {
  display: "inline-block",
  width: "8px",
  height: "8px",
  borderRadius: "50%",
  backgroundColor: "#e53e3e",
  marginLeft: "6px",
  verticalAlign: "middle",
  opacity: 0.9,
};

export default function StaleIndicator({
  fetchedAt,
  thresholdMinutes = 20,
}: StaleIndicatorProps) {
  const [isStale, setIsStale] = useState(false);

  useEffect(() => {
    if (!fetchedAt) {
      setIsStale(false);
      return;
    }

    const check = () => {
      const ageMs = Date.now() - new Date(fetchedAt).getTime();
      setIsStale(ageMs > thresholdMinutes * 60 * 1000);
    };

    check();
    const id = setInterval(check, 60_000);
    return () => clearInterval(id);
  }, [fetchedAt, thresholdMinutes]);

  if (!isStale) return null;

  return <span style={STYLE} title="Data is stale (not updated recently)" />;
}
