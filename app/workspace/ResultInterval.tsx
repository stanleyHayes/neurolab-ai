export function finiteMeasure(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}
export function ResultInterval({
  estimate,
  interval,
  formatNumber,
}: Readonly<{
  estimate: unknown;
  interval: unknown;
  formatNumber: (value: unknown) => string;
}>) {
  const center = finiteMeasure(estimate);
  const low = Array.isArray(interval) ? finiteMeasure(interval[0]) : null;
  const high = Array.isArray(interval) ? finiteMeasure(interval[1]) : null;
  if (center === null || low === null || high === null || low > high)
    return (
      <p className="caption">No valid interval was recorded for this result.</p>
    );
  const minimum = Math.min(low, center, 0);
  const maximum = Math.max(high, center, 0);
  const padding = Math.max((maximum - minimum) * 0.12, 1);
  const domainMin = minimum - padding;
  const domainMax = maximum + padding;
  const x = (value: number) =>
    36 + ((value - domainMin) / (domainMax - domainMin)) * 488;
  const ticks = [domainMin, (domainMin + domainMax) / 2, domainMax];
  return (
    <figure className="result-interval-figure">
      <svg
        viewBox="0 0 560 112"
        role="img"
        aria-label={`Observed drought-minus-well-watered difference ${formatNumber(center)} kg/ha; 95% block-bootstrap interval ${formatNumber(low)} to ${formatNumber(high)} kg/ha.`}
      >
        <line className="interval-zero" x1={x(0)} x2={x(0)} y1="14" y2="71" />
        <text
          className="interval-zero-label"
          x={x(0)}
          y="10"
          textAnchor="middle"
        >
          No difference
        </text>
        <line className="interval-axis" x1="36" x2="524" y1="72" y2="72" />
        {ticks.map((tick) => (
          <g key={tick}>
            <line
              className="interval-axis"
              x1={x(tick)}
              x2={x(tick)}
              y1="72"
              y2="77"
            />
            <text
              className="interval-tick"
              x={x(tick)}
              y="94"
              textAnchor="middle"
            >
              {formatNumber(tick)}
            </text>
          </g>
        ))}
        <line
          className="interval-estimate-line"
          x1={x(low)}
          x2={x(high)}
          y1="45"
          y2="45"
        />
        <line
          className="interval-cap"
          x1={x(low)}
          x2={x(low)}
          y1="35"
          y2="55"
        />
        <line
          className="interval-cap"
          x1={x(high)}
          x2={x(high)}
          y1="35"
          y2="55"
        />
        <circle
          className="interval-estimate-dot"
          cx={x(center)}
          cy="45"
          r="6"
        />
      </svg>
      <figcaption>
        <span className="interval-legend-dot" />
        <span>Observed contrast</span>
        <span className="interval-legend-line" />
        <span>95% block-bootstrap interval</span>
        <span>kg/ha</span>
      </figcaption>
    </figure>
  );
}
