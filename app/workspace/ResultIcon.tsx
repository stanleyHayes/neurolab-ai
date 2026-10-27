const PATHS = {
  comparison: "M4 7h12m-3-3 3 3-3 3M20 17H8m3-3-3 3 3 3M4 14v6M20 4v6",
  interval: "M4 12h16M4 8v8m16-8v8M12 8v8",
  plots: "M5 5h5v5H5zM14 5h5v5h-5zM5 14h5v5H5zM14 14h5v5h-5z",
  genotype:
    "M7 3c0 5 10 5 10 10s-10 5-10 8M17 3c0 5-10 5-10 10s10 5 10 8M8 6h8m-7 5h6m-6 5h6",
  retention: "M19 8a8 8 0 1 0 1 8M19 3v5h-5M12 8v5l3 2",
  source:
    "M8 4h10a2 2 0 0 1 2 2v10M16 8H6a2 2 0 0 0-2 2v10h12V8ZM8 12h4m-4 4h4",
  method:
    "M9 3h6m-5 0v6L5 18a2 2 0 0 0 2 3h10a2 2 0 0 0 2-3l-5-9V3M8 15h8m-5 3h2",
  caution:
    "M12 3 2.8 19a1.3 1.3 0 0 0 1.1 2h16.2a1.3 1.3 0 0 0 1.1-2L12 3Zm0 6v5m0 3v.1",
  download: "M12 3v12m-4-4 4 4 4-4M4 15v5h16v-5",
  record: "M8 3H5v18h14V3h-3M9 2h6v4H9zM8 11h8m-8 4h5",
  complete: "m5 12 4 4L19 6M4 4v3m16 10v3",
  evidence: "M4 18V9m5 9V5m5 13v-7m5 7V3M3 21h18",
} as const;

export function ResultIcon({
  name,
  className = "",
}: Readonly<{ name: keyof typeof PATHS; className?: string }>) {
  return (
    <svg
      className={`result-icon ${className}`}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      <path d={PATHS[name]} />
    </svg>
  );
}
