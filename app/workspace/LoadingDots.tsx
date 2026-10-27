export function LoadingDots() {
  return (
    <>
      <span className="loading-dots" aria-hidden="true">
        <span />
        <span />
        <span />
      </span>
      <span className="sr-only">Loading</span>
    </>
  );
}
