import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getDashboard, listProjects } from "../api";
import { useAuth } from "../AuthContext";
import { FormTypesTab } from "../components/FormTypesTab";
import { ProjectList } from "../components/ProjectList";
import { StatusDistributionChart } from "../components/StatusDistributionChart";
import { UploadTrendChart } from "../components/UploadTrendChart";
import { UserManagement } from "../components/UserManagement";
import type { DashboardStats, Project } from "../types";

function errorMessage(err: unknown): string {
  return err instanceof Error ? err.message : "Something went wrong.";
}

function formatSeconds(s: number | null): string {
  if (s == null) return "—";
  return s < 60 ? `${s.toFixed(1)}s` : `${(s / 60).toFixed(1)}m`;
}

type Tab = "overview" | "projects" | "users" | "types";

export function HomePage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const isAdmin = user?.role === "admin";
  const [tab, setTab] = useState<Tab>("overview");
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
      {stats && (
        <div className="stat-grid stat-grid--top">
          {isAdmin && (
            <div className="stat-card">
              <span className="stat-label">Total Users</span>
              <span className="stat-value">{stats.total_users}</span>
            </div>
          )}
          <div className="stat-card">
            <span className="stat-label">Total Projects</span>
            <span className="stat-value">{stats.total_projects}</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Total Uploads</span>
            <span className="stat-value">{stats.total_documents}</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Avg Processing Time</span>
            <span className="stat-value">{formatSeconds(stats.avg_processing_seconds)}</span>
          </div>
        </div>
      )}

      {error && (
        <div className="error-banner">
          <span>{error}</span>
          <button onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}

      <div className="section-tabs section-tabs--top">
        <button
          className={`section-tab ${tab === "overview" ? "section-tab--active" : ""}`}
          onClick={() => setTab("overview")}
        >
          Overview
        </button>
        <button
          className={`section-tab ${tab === "projects" ? "section-tab--active" : ""}`}
          onClick={() => setTab("projects")}
        >
          Projects
        </button>
        {isAdmin && (
          <button
            className={`section-tab ${tab === "users" ? "section-tab--active" : ""}`}
            onClick={() => setTab("users")}
          >
            User Management
          </button>
        )}
        <button
          className={`section-tab ${tab === "types" ? "section-tab--active" : ""}`}
          onClick={() => setTab("types")}
        >
          Form Types
        </button>
      </div>

      {tab === "overview" && stats && (
        <div className="charts-grid">
          <UploadTrendChart data={stats.daily_uploads} />
          <StatusDistributionChart statusCounts={stats.status_counts} />
        </div>
      )}

      {tab === "projects" && (
        <ProjectList
          projects={projects}
          onSelect={(p) => navigate(`/projects/${p.id}/upload`)}
          onCreated={refresh}
          onError={(err) => setError(errorMessage(err))}
        />
      )}

      {tab === "users" && isAdmin && <UserManagement />}

      {tab === "types" && <FormTypesTab />}
    </div>
  );
}
