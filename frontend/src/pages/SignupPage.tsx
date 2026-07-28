import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../AuthContext";

export function SignupPage() {
  const { signup } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await signup(email, password);
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
        <img src="/brand/datafactz-logo.png" alt="DataFactZ" className="signin-logo signin-logo--light" />
        <img
          src="/brand/datafactz-logo-dark.png"
          alt="DataFactZ"
          className="signin-logo signin-logo--dark"
        />
        <p className="signin-tagline">Document Extraction</p>
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
