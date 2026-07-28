import type { DocumentStatus } from "../types";

const LABELS: Record<DocumentStatus, string> = {
  queued: "Queued",
  parsing: "Parsing",
  extracting: "Extracting",
  escalated: "Escalated",
  needs_review: "Needs review",
  approved: "Approved",
  failed: "Failed",
};

export function StatusBadge({ status }: { status: DocumentStatus }) {
  return <span className={`badge badge-${status}`}>{LABELS[status] ?? status}</span>;
}
