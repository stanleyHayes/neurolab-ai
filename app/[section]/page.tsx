import { notFound } from "next/navigation";
import { ResearchWorkspace } from "../research-workspace";
import { WORKSPACE_SECTIONS } from "../workspace/workspace-config";
import type { WorkspaceSection } from "../workspace/workspace-types";

const ROUTE_SECTIONS = WORKSPACE_SECTIONS.filter(
  (section) => section !== "overview",
);

export function generateStaticParams() {
  return ROUTE_SECTIONS.map((section) => ({ section }));
}

export default async function WorkspaceSectionPage({
  params,
}: Readonly<{
  params: Promise<{ section: string }>;
}>) {
  const { section } = await params;
  if (
    !ROUTE_SECTIONS.includes(section as Exclude<WorkspaceSection, "overview">)
  )
    notFound();
  return <ResearchWorkspace section={section as WorkspaceSection} />;
}
