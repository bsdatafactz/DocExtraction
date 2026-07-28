import { NavLink, useParams } from "react-router-dom";
import { useAuth } from "../AuthContext";
import { ThemeToggle } from "./ThemeToggle";

export function TopNav() {
  const { user, logout } = useAuth();
  const { projectId } = useParams();

  return (
    <nav className="top-nav">
      <div className="top-nav-left">
        <NavLink to="/" className="top-nav-brand">
          <img src="/brand/datafactz-mark.png" alt="" className="top-nav-logo" />
          <span>
            DataFactZ <span className="top-nav-brand-sub">Document Extraction</span>
          </span>
        </NavLink>
        <NavLink to="/" end className={({ isActive }) => (isActive ? "nav-link nav-link--active" : "nav-link")}>
          Home
        </NavLink>
        {projectId && (
          <>
            <NavLink
              to={`/projects/${projectId}/upload`}
              className={({ isActive }) => (isActive ? "nav-link nav-link--active" : "nav-link")}
            >
              Upload
            </NavLink>
            <NavLink
              to={`/projects/${projectId}/review`}
              className={({ isActive }) => (isActive ? "nav-link nav-link--active" : "nav-link")}
            >
              Review
            </NavLink>
          </>
        )}
      </div>
      <div className="header-actions">
        <span className="role-badge">{user?.role === "admin" ? "Admin" : "User"}</span>
        <button className="signout-link" onClick={logout}>
          Sign out
        </button>
        <ThemeToggle />
      </div>
    </nav>
  );
}
