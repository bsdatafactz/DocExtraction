export type DocumentType = "invoice" | "resume" | "contract";

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

interface ExtractionMeta {
  field_status: Record<string, FieldStatus>;
  self_reported_confidence: Record<string, number>;
}

export interface InvoiceExtraction extends ExtractionMeta {
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
}

export interface WorkExperience {
  company: string;
  title: string | null;
  start_date: string | null;
  end_date: string | null;
  description: string | null;
}

export interface ResumeProject {
  name: string;
  description: string | null;
  technologies: string | null;
}

export interface Education {
  institution: string;
  degree: string | null;
  field_of_study: string | null;
  graduation_year: string | null;
}

export interface ResumeExtraction extends ExtractionMeta {
  full_name: string | null;
  email: string | null;
  phone: string | null;
  professional_summary: string | null;
  skills: string[];
  work_experience: WorkExperience[];
  projects: ResumeProject[];
  education: Education[];
}

export type Extraction = InvoiceExtraction | ResumeExtraction;

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
  document_type: DocumentType;
  extraction: Extraction | null;
  confidence: DocumentConfidence | null;
}

export interface DailyCount {
  date: string;
  count: number;
}

export interface DashboardStats {
  total_users: number;
  total_projects: number;
  total_documents: number;
  status_counts: Record<string, number>;
  avg_parsing_seconds: number | null;
  avg_extraction_seconds: number | null;
  avg_processing_seconds: number | null;
  scanned_count: number;
  error_count: number;
  error_rate: number;
  escalation_count: number;
  escalation_rate: number;
  auto_approved_count: number;
  reviewed_count: number;
  daily_uploads: DailyCount[];
}
