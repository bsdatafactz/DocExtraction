import { getStoredToken } from "./auth";
import type {
  DashboardStats,
  DocumentDetail,
  DocumentSummary,
  DocumentType,
  Project,
} from "./types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

function authHeaders(): Record<string, string> {
  const token = getStoredToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${BASE_URL}/api/v1${path}`, {
    ...init,
    headers: { ...authHeaders(), ...init.headers },
  });
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

export function getDashboard(): Promise<DashboardStats> {
  return request("/dashboard");
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
