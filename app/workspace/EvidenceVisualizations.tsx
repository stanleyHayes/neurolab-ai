import { finiteMeasure } from "./ResultInterval";

type Row = Record<string, unknown>;
const number = (value: number, digits = 1) =>
  value.toLocaleString(undefined, { maximumFractionDigits: digits });
const identifier = (value: unknown) =>
  typeof value === "string" ? value : "Not recorded";
const label = (value: unknown) =>
  typeof value === "string" ? value.replaceAll("_", " ") : "Not recorded";

export function MetricVisual({
  value,
  maximum,
  reference,
  description,
}: Readonly<{
  value: unknown;
  maximum: number;
  reference?: number;
  description: string;
}>) {
  const amount = finiteMeasure(value);
  if (
    amount === null ||
    amount < 0 ||
    !Number.isFinite(maximum) ||
    maximum <= 0
  )
    return null;
  const domain = Math.max(maximum, amount, reference ?? 0);
  let referenceDescription = "";
  let scaleLabel = `${number(domain)} kg/ha`;
  if (reference !== undefined) {
    referenceDescription = `; reference ${number(reference)}`;
    scaleLabel = `${number(reference)}% reference`;
    if (domain > reference) scaleLabel += ` · scale to ${number(domain)}%`;
  }
  return (
    <figure className="metric-visual">
      <svg
        viewBox="0 0 240 28"
        role="img"
        aria-label={`${description}: ${number(amount)}; scale 0 to ${number(domain)}${referenceDescription}`}
      >
        <rect
          className="metric-visual-track"
          x="1"
          y="9"
          width="238"
          height="10"
          rx="5"
        />
        <rect
          className="metric-visual-fill"
          x="1"
          y="9"
          width={(238 * amount) / domain}
          height="10"
          rx="5"
        />
        {reference !== undefined && (
          <path
            className="metric-visual-reference"
            d={`M${1 + (238 * reference) / domain} 3v22`}
          />
        )}
      </svg>
      <figcaption>
        <span>0</span>
        <span>{scaleLabel}</span>
      </figcaption>
    </figure>
  );
}

export function InlineMeasure({
  value,
  maximum,
  formatted,
}: Readonly<{ value: unknown; maximum: number; formatted: string }>) {
  const amount = finiteMeasure(value);
  return (
    <span className="inline-evidence-measure">
      <span>{formatted}</span>
      {amount !== null &&
        amount >= 0 &&
        maximum > 0 &&
        Number.isFinite(maximum) && (
          <span className="inline-evidence-track" aria-hidden="true">
            <span
              style={{
                width: `${(amount / Math.max(maximum, amount)) * 100}%`,
              }}
            />
          </span>
        )}
    </span>
  );
}

export function GenotypeMiniPlot({ entries }: Readonly<{ entries: Row[] }>) {
  const measured = entries
    .map((entry) => ({
      id: identifier(entry.genotype_id),
      value: finiteMeasure(entry.equal_environment_mean_yield_kg_ha),
    }))
    .filter(
      (entry): entry is { id: string; value: number } =>
        entry.value !== null && entry.value >= 0,
    );
  if (!measured.length) return null;
  const maximum = Math.max(...measured.map((entry) => entry.value), 1);
  const step = 240 / measured.length;
  return (
    <figure className="metric-visual genotype-mini-plot">
      <svg
        viewBox="0 0 240 38"
        role="img"
        aria-label={`${measured.length} recorded genotype mean yields in saved order, zero-based scale to ${number(maximum)} kg/ha`}
      >
        {measured.map((entry, index) => (
          <rect
            key={`${entry.id}-${index}`}
            x={index * step}
            y={36 - (34 * entry.value) / maximum}
            width={Math.max(step * 0.7, 0.2)}
            height={(34 * entry.value) / maximum}
          >
            <title>
              {entry.id}: {number(entry.value)} kg/ha
            </title>
          </rect>
        ))}
      </svg>
      <figcaption>Recorded mean yields · kg/ha · saved order</figcaption>
    </figure>
  );
}

function associationInterval(value: unknown): [number, number] | null {
  if (!Array.isArray(value)) return null;
  const low = finiteMeasure(value[0]);
  const high = finiteMeasure(value[1]);
  return low !== null && high !== null && low >= -1 && high <= 1 && low <= high
    ? [low, high]
    : null;
}
export function TraitAssociationPlot({
  associations,
}: Readonly<{ associations: Row[] }>) {
  if (!associations.length) return null;
  const x = (value: number) => 12 + (value + 1) * 148;
  return (
    <figure className="evidence-comparison-plot">
      <figcaption>
        <strong>Trait direction at a glance</strong>
        <span>
          Dots show recorded correlations; lines show the saved 95%
          genotype-resampling intervals. Zero means no rank association. These
          are exploratory associations, not causal effects.
        </span>
      </figcaption>
      <div className="association-plot-axis" aria-hidden="true">
        <span>−1 · negative</span>
        <span>0</span>
        <span>+1 · positive</span>
      </div>
      {associations.map((entry, index) => {
        const raw = finiteMeasure(entry.spearman_rho);
        const value = raw !== null && Math.abs(raw) <= 1 ? raw : null;
        const interval = associationInterval(
          entry.spearman_rho_95_percentile_interval,
        );
        const trait = label(entry.trait);
        const intervalDescription = interval
          ? `95% conditional resampling interval ${number(interval[0], 3)} to ${number(interval[1], 3)}`
          : "interval not estimated";
        return (
          <div className="association-plot-row" key={`${trait}-${index}`}>
            <span>{trait}</span>
            {value === null ? (
              <span className="plot-missing">Not recorded</span>
            ) : (
              <svg
                viewBox="0 0 320 36"
                role="img"
                aria-label={`${trait}: Spearman rho ${number(value, 3)}; ${intervalDescription}`}
              >
                <path className="comparison-axis" d="M12 18H308" />
                <path className="comparison-zero" d={`M${x(0)} 2v32`} />
                {interval && (
                  <g className="comparison-range">
                    <path
                      d={`M${x(interval[0])} 18H${x(interval[1])}M${x(interval[0])} 12v12M${x(interval[1])} 12v12`}
                    />
                  </g>
                )}
                <circle
                  className={
                    value < 0 ? "association-negative" : "association-positive"
                  }
                  cx={x(value)}
                  cy="18"
                  r="5"
                />
              </svg>
            )}
            <strong>{value === null ? "—" : number(value, 3)}</strong>
          </div>
        );
      })}
      <p className="caption">
        An interval crossing zero includes both directions. A missing interval
        is not drawn as zero uncertainty. Exact values and per-environment
        associations remain in the table below.
      </p>
    </figure>
  );
}

type EnvironmentPoint = { environment: string; value: number };
function environmentPoints(entry: Row): EnvironmentPoint[] {
  if (!Array.isArray(entry.environment_means)) return [];
  return entry.environment_means.flatMap((item: Row) => {
    const value = finiteMeasure(item?.mean_yield_kg_ha);
    return typeof item?.environment_code === "string" &&
      value !== null &&
      value >= 0
      ? [{ environment: item.environment_code, value }]
      : [];
  });
}
export function EnvironmentYieldPlot({
  entries,
  environments,
  regime,
}: Readonly<{ entries: Row[]; environments: unknown[]; regime: string }>) {
  const visible = entries.slice(0, 8).map((entry) => ({
    id: identifier(entry.genotype_id),
    points: environmentPoints(entry),
  }));
  const values = visible.flatMap((entry) =>
    entry.points.map((point) => point.value),
  );
  if (!values.length) return null;
  const maximum = Math.max(Math.ceil(Math.max(...values) / 1000) * 1000, 1000);
  const x = (value: number) => 12 + (value / maximum) * 296;
  const codes = [
    ...new Set([
      ...environments.filter(
        (code): code is string => typeof code === "string",
      ),
      ...visible.flatMap((entry) =>
        entry.points.map((point) => point.environment),
      ),
    ]),
  ];
  return (
    <figure className="evidence-comparison-plot environment-yield-plot">
      <figcaption>
        <strong>Observed yields across environments · {label(regime)}</strong>
        <span>
          First {visible.length} saved genotype summaries. Each symbol is a
          recorded environment mean; the connecting line spans their observed
          range, not a confidence interval or a future prediction.
        </span>
      </figcaption>
      <div className="environment-plot-legend">
        {codes.map((code, index) => (
          <span key={code}>
            <i
              className={`environment-symbol environment-symbol-${index % 3}`}
              aria-hidden="true"
            />
            {code}
          </span>
        ))}
      </div>
      <div className="environment-plot-axis" aria-hidden="true">
        <span>0</span>
        <span>{number(maximum / 2)}</span>
        <span>{number(maximum)} kg/ha</span>
      </div>
      {visible.map((entry, index) => (
        <div className="environment-plot-row" key={`${entry.id}-${index}`}>
          <span>{entry.id}</span>
          {entry.points.length ? (
            <svg
              viewBox="0 0 320 36"
              role="img"
              aria-label={[
                entry.id + ":",
                entry.points
                  .map(
                    (point) =>
                      `${point.environment} ${number(point.value)} kg/ha`,
                  )
                  .join("; "),
              ].join(" ")}
            >
              <path className="comparison-axis" d="M12 18H308" />
              <path
                className="comparison-range"
                d={`M${x(Math.min(...entry.points.map((point) => point.value)))} 18H${x(Math.max(...entry.points.map((point) => point.value)))}`}
              />
              {entry.points.map((point) => {
                const kind = Math.max(codes.indexOf(point.environment), 0) % 3;
                const title = (
                  <title>
                    {point.environment}: {number(point.value)} kg/ha
                  </title>
                );
                return (
                  <g
                    key={point.environment}
                    className={`environment-point environment-point-${kind}`}
                  >
                    {kind === 0 && (
                      <circle cx={x(point.value)} cy="18" r="4.5">
                        {title}
                      </circle>
                    )}
                    {kind === 1 && (
                      <rect x={x(point.value) - 4} y="14" width="8" height="8">
                        {title}
                      </rect>
                    )}
                    {kind === 2 && (
                      <path d={`M${x(point.value)} 12l6 10h-12Z`}>{title}</path>
                    )}
                  </g>
                );
              })}
            </svg>
          ) : (
            <span className="plot-missing">Not recorded</span>
          )}
        </div>
      ))}
      <p className="caption">
        Shared zero-based scale within this regime. Environment codes are source
        identifiers, not calendar years. All recorded values and coverage
        details remain below.
      </p>
    </figure>
  );
}
