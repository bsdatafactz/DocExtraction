export type DocumentType = "invoice" | "resume" | "purchase_order" | "contract";

export interface Project {
  id: number;
  name: string;
  document_type: DocumentType;
  created_at: string;
  is_implemented: boolean;
}

export type DocumentStatus =
  | "queued"
  | "parsing"
  | "extracting"
  | "escalated"
  | "needs_review"
  | "approved"
  | "failed";

export interface LineItem {
  description: string;
  quantity: number | null;
  unit_price: number | null;
  line_total: number | null;
}

export type FieldStatus = "extracted" | "not_applicable" | "illegible";

export interface InvoiceExtraction {
  invoice_number: string | null;
  invoice_date: string | null;
  due_date: string | null;
  po_number: string | null;
  vendor_name: string | null;
  vendor_address: string | null;
  vendor_tax_id: string | null;
  customer_name: string | null;
  customer_address: string | null;
  currency: string | null;
  subtotal: number | null;
  tax_amount: number | null;
  total_amount: number | null;
  payment_terms: string | null;
  line_items: LineItem[];
  field_status: Record<string, FieldStatus>;
  self_reported_confidence: Record<string, number>;
}

export interface FieldConfidence {
  field_name: string;
  self_reported: number;
  heuristic_score: number;
  composite: number;
  escalated: boolean;
  cross_model_agreement: boolean | null;
}

export interface DocumentConfidence {
  document_id: number;
  fields: FieldConfidence[];
  aggregate: number;
  needs_review: boolean;
}

export interface DocumentSummary {
  id: number;
  filename: string;
  status: DocumentStatus;
  created_at: string;
  aggregate_confidence: number | null;
}

export interface DocumentDetail extends DocumentSummary {
  extraction: InvoiceExtraction | null;
  confidence: DocumentConfidence | null;
}

export interface DashboardStats {
  total_projects: number;
  total_documents: number;
  status_counts: Record<string, number>;
  avg_parsing_seconds: number | null;
  avg_extraction_seconds: number | null;
  scanned_count: number;
  error_count: number;
  error_rate: number;
  escalation_count: number;
  escalation_rate: number;
  auto_approved_count: number;
  reviewed_count: number;
}
