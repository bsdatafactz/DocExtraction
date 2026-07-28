import type { DocumentType } from "./types";

export const DOCUMENT_TYPES: Array<{ value: DocumentType; label: string; implemented: boolean }> = [
  { value: "invoice", label: "Invoices", implemented: true },
  { value: "resume", label: "Resumes", implemented: true },
  { value: "contract", label: "Contracts", implemented: false },
];
