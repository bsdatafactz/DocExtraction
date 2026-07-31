import { getStoredToken } from "./auth";
import type {
  CostSummary,
  DashboardStats,
  DocumentDetail,
  DocumentSummary,
  DocumentType,
  Project,
} from "./types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

// Plain fetch() has no timeout — if the backend is slow (e.g. an OCR job
// hogging the CPU), a request just hangs forever instead of failing, so the
// page never gets a chance to show an error and just sits blank. Force a
// bound so slow polls fail fast with a clear message instead.
const REQUEST_TIMEOUT_MS = 20_000;

function authHeaders(): Record<string, string> {
  const token = getStoredToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}/api/v1${path}`, {
      ...init,
      headers: { ...authHeaders(), ...init.headers },
      signal: controller.signal,
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new Error("Request timed out — the server is taking longer than expected.");
    }
    throw err;
  } finally {
    clearTimeout(timeout);
  }
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`${response.status} ${response.statusText}: ${body}`);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

// ---- Auth ----

export interface AuthResponse {
  access_token: string;
  user: { id: number; email: string; role: "admin" | "user"; created_at: string };
}

export function signup(email: string, password: string): Promise<AuthResponse> {
  return request("/auth/signup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
}

export function login(email: string, password: string): Promise<AuthResponse> {
  return request("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
}

// ---- Projects ----

export function listProjects(): Promise<Project[]> {
  return request("/projects");
}

export function createProject(name: string, documentType: DocumentType): Promise<Project> {
  return request("/projects", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, document_type: documentType }),
  });
}

export function deleteProject(id: number): Promise<void> {
  return request(`/projects/${id}`, { method: "DELETE" });
}

// ---- Documents ----

export function listDocuments(projectId: number, status?: string): Promise<DocumentSummary[]> {
  const query = status ? `?status=${status}` : "";
  return request(`/projects/${projectId}/documents${query}`);
}

export function getDocument(id: number): Promise<DocumentDetail> {
  return request(`/documents/${id}`);
}

// <img>/pdf.js can't attach an Authorization header, so the file endpoint
// also accepts the token as a query param — see documents.py.
export function documentFileUrl(id: number): string {
  const token = getStoredToken() ?? "";
  return `${BASE_URL}/api/v1/documents/${id}/file?token=${encodeURIComponent(token)}`;
}

export async function uploadDocument(projectId: number, file: File): Promise<DocumentSummary> {
  const formData = new FormData();
  formData.append("file", file);
  return request(`/projects/${projectId}/documents`, { method: "POST", body: formData });
}

export function deleteDocument(id: number): Promise<void> {
  return request(`/documents/${id}`, { method: "DELETE" });
}

// A plain <a href> can't attach an Authorization header, so exports are
// fetched with auth then handed to the browser as a Blob download instead.
async function downloadExport(path: string, fallbackFilename: string): Promise<void> {
  const response = await fetch(`${BASE_URL}/api/v1${path}`, { headers: authHeaders() });
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}: ${await response.text()}`);
  }
  const disposition = response.headers.get("Content-Disposition") ?? "";
  const match = disposition.match(/filename="?([^"]+)"?/);
  const filename = match ? match[1] : fallbackFilename;

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = window.document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

export function exportDocument(id: number, format: "json" | "csv"): Promise<void> {
  return downloadExport(`/documents/${id}/export?format=${format}`, `document-${id}.${format}`);
}

export function exportProjectDocuments(
  projectId: number,
  format: "json" | "csv",
): Promise<void> {
  return downloadExport(
    `/projects/${projectId}/documents/export?format=${format}`,
    `project-${projectId}.${format}`,
  );
}

export function submitCorrections(
  id: number,
  correctedFields: Record<string, string | number | null | Record<string, unknown>[]>,
  approve: boolean,
): Promise<DocumentDetail> {
  return request(`/documents/${id}/corrections`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ corrected_fields: correctedFields, approve }),
  });
}

// ---- Dashboard ----

export function getDashboard(projectId?: number): Promise<DashboardStats> {
  const query = projectId != null ? `?project_id=${projectId}` : "";
  return request(`/dashboard${query}`);
}

// ---- Cost ----

export function getCostSummary(): Promise<CostSummary> {
  return request("/cost");
}

// ---- Users (admin only) ----

export interface UserSummary {
  id: number;
  email: string;
  role: "admin" | "user";
  created_at: string;
}

export function listUsers(): Promise<UserSummary[]> {
  return request("/users");
}

export function updateUserRole(id: number, role: "admin" | "user"): Promise<UserSummary> {
  return request(`/users/${id}/role`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ role }),
  });
}

export function deleteUser(id: number): Promise<void> {
  return request(`/users/${id}`, { method: "DELETE" });
}
