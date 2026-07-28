import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getDashboard, listProjects } from "../api";
import { useAuth } from "../AuthContext";
import { ProjectList } from "../components/ProjectList";
import type { DashboardStats, Project } from "../types";

function errorMessage(err: unknown): string {
  return err instanceof Error ? err.message : "Something went wrong.";
}

function formatSeconds(s: number | null): string {
  if (s == null) return "—";
  return s < 60 ? `${s.toFixed(1)}s` : `${(s / 60).toFixed(1)}m`;
}

export function HomePage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [statsRes, projectsRes] = await Promise.all([getDashboard(), listProjects()]);
      setStats(statsRes);
      setProjects(projectsRes);
    } catch (err) {
      setError(errorMessage(err));
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return (
    <div>
      {error && (
        <div className="error-banner">
          <span>{error}</span>
          <button onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}

      {stats && (
        <div className="stat-grid">
          <div className="stat-card">
            <span className="stat-label">Total projects</span>
            <span className="stat-value">{stats.total_projects}</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Total documents</span>
            <span className="stat-value">{stats.total_documents}</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Needs review</span>
            <span className="stat-value">{stats.status_counts.needs_review ?? 0}</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Auto-approved (≥90%)</span>
            <span className="stat-value">{stats.auto_approved_count}</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Manually reviewed</span>
            <span className="stat-value">{stats.reviewed_count}</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Scanned documents</span>
            <span className="stat-value">{stats.scanned_count}</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Avg. parsing time</span>
            <span className="stat-value">{formatSeconds(stats.avg_parsing_seconds)}</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Avg. extraction time</span>
            <span className="stat-value">{formatSeconds(stats.avg_extraction_seconds)}</span>
          </div>
          <div className="stat-card stat-card--warn">
            <span className="stat-label">Escalated to stronger model</span>
            <span className="stat-value">
              {stats.escalation_count}{" "}
              <span className="stat-sub">({Math.round(stats.escalation_rate * 100)}%)</span>
            </span>
          </div>
          <div className="stat-card stat-card--error">
            <span className="stat-label">Failed</span>
            <span className="stat-value">
              {stats.error_count}{" "}
              <span className="stat-sub">({Math.round(stats.error_rate * 100)}%)</span>
            </span>
          </div>
        </div>
      )}

      <h2 className="section-heading">Projects</h2>
      <ProjectList
        projects={projects}
        onSelect={(p) => navigate(`/projects/${p.id}/upload`)}
        onCreated={refresh}
        onError={(err) => setError(errorMessage(err))}
        isAdmin={user?.role === "admin"}
      />
    </div>
  );
}
