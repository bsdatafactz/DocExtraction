import { createContext, useContext, useState, type ReactNode } from "react";
import * as api from "./api";
import { clearAuth, getStoredToken, getStoredUser, setAuth, type AuthUser, type Role } from "./auth";

interface AuthContextValue {
  user: AuthUser | null;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, role: Role) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(() =>
    getStoredToken() ? getStoredUser() : null,
  );

  async function login(email: string, password: string) {
    const res = await api.login(email, password);
    setAuth(res.access_token, res.user);
    setUser(res.user);
  }

  async function signup(email: string, password: string, role: Role) {
    const res = await api.signup(email, password, role);
    setAuth(res.access_token, res.user);
    setUser(res.user);
  }

  function logout() {
    clearAuth();
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, login, signup, logout }}>{children}</AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
