import { NavLink } from "react-router-dom";
import { useAuth } from "../AuthContext";
import { ThemeToggle } from "./ThemeToggle";

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  isActive ? "nav-link nav-link--active" : "nav-link";

export function TopNav() {
  const { user, logout } = useAuth();
  const isAdmin = user?.role === "admin";

  return (
    <nav className="top-nav">
      <div className="top-nav-left">
        <NavLink to="/" className="top-nav-brand">
          <img src="/brand/datafactz-mark.png" alt="" className="top-nav-logo" />
          <span>
            DataFactZ <span className="top-nav-brand-sub">Document Extraction</span>
          </span>
        </NavLink>
        <NavLink to="/" end className={navLinkClass}>
          Overview
        </NavLink>
        <NavLink to="/projects" className={navLinkClass}>
          Projects
        </NavLink>
        {isAdmin && (
          <NavLink to="/users" className={navLinkClass}>
            User Management
          </NavLink>
        )}
        <NavLink to="/types" className={navLinkClass}>
          Form Types
        </NavLink>
        <NavLink to="/cost" className={navLinkClass}>
          Usage &amp; Cost
        </NavLink>
      </div>
      <div className="header-actions">
        <span className="role-badge">{isAdmin ? "Admin" : "User"}</span>
        <button className="signout-link" onClick={logout}>
          Sign out
        </button>
        <ThemeToggle />
      </div>
    </nav>
  );
}
