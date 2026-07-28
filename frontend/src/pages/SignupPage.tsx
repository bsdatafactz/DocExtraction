import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../AuthContext";
import type { Role } from "../auth";

export function SignupPage() {
  const { signup } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<Role>("user");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await signup(email, password, role);
      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Signup failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="signin">
      <div className="signin-card">
        <h1>Invoice Extraction</h1>
        <p>Create an account.</p>
        <form className="auth-form" onSubmit={handleSubmit}>
          {error && <div className="error-banner">{error}</div>}
          <label>
            <span className="field-name">Email</span>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoFocus
            />
          </label>
          <label>
            <span className="field-name">Password</span>
            <input
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </label>

          <span className="field-name">Account type</span>
          <div className="doctype-options">
            <button
              type="button"
              className={`doctype-option ${role === "user" ? "doctype-option--selected" : ""}`}
              onClick={() => setRole("user")}
            >
              User
              <span className="doctype-soon">Upload, review, approve</span>
            </button>
            <button
              type="button"
              className={`doctype-option ${role === "admin" ? "doctype-option--selected" : ""}`}
              onClick={() => setRole("admin")}
            >
              Admin
              <span className="doctype-soon">Full access + delete</span>
            </button>
          </div>

          <button className="btn btn-primary" disabled={submitting} type="submit">
            {submitting ? "Creating account…" : "Create account"}
          </button>
        </form>
        <p className="auth-switch">
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
