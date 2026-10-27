import { ErrorPanel } from "./ErrorPanel";
import type { ErrorContext } from "./workspace-types";

type ErrorCopy = {
  title: string;
  description: string;
  action: string;
  retry: () => void | Promise<void>;
};

type WorkspaceErrorItemProps = {
  context: ErrorContext;
  details: string;
  copy: ErrorCopy;
  retrying: boolean;
  onRetry: (
    context: ErrorContext,
    retry: () => void | Promise<void>,
  ) => Promise<void>;
};

export function WorkspaceErrorItem({
  context,
  details,
  copy,
  retrying,
  onRetry,
}: Readonly<WorkspaceErrorItemProps>) {
  return (
    <ErrorPanel
      title={copy.title}
      description={copy.description}
      details={details}
      actionLabel={copy.action}
      onRetry={() => void onRetry(context, copy.retry)}
      busy={retrying}
    />
  );
}
