// Real backend-verified auth: the JWT issued by /api/v1/auth/login|signup is
// stored here and sent as a Bearer token on every request (see api.ts). The
// backend independently re-checks the role on every protected endpoint —
// this is not just a UI convenience layer like the earlier version was.

export type Role = "admin" | "user";

export interface AuthUser {
  id: number;
  email: string;
  role: Role;
}

const TOKEN_KEY = "auth_token";
const USER_KEY = "auth_user";

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser(): AuthUser | null {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as AuthUser;
  } catch {
    return null;
  }
}

export function setAuth(token: string, user: AuthUser) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearAuth() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}
