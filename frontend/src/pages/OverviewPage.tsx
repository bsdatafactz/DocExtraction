import { useCallback, useEffect, useState } from "react";
import { getDashboard } from "../api";
import { useAuth } from "../AuthContext";
import { StatusDistributionChart } from "../components/StatusDistributionChart";
import { UploadTrendChart } from "../components/UploadTrendChart";
import type { DashboardStats } from "../types";

function errorMessage(err: unknown): string {
  return err instanceof Error ? err.message : "Something went wrong.";
}

function formatSeconds(s: number | null): string {
  if (s == null) return "—";
  return s < 60 ? `${s.toFixed(1)}s` : `${(s / 60).toFixed(1)}m`;
}

export function OverviewPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setStats(await getDashboard());
    } catch (err) {
      setError(errorMessage(err));
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return (
    <div>
      {stats == null && error == null && <p className="page-subtitle">Loading…</p>}

      {error && (
        <div className="error-banner">
          <span>{error}</span>
          <button onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}

      {stats && (
        <>
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

          <div className="charts-grid">
            <UploadTrendChart data={stats.daily_uploads} />
            <StatusDistributionChart statusCounts={stats.status_counts} />
          </div>
        </>
      )}
    </div>
  );
}
