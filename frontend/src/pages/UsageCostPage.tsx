import { useCallback, useEffect, useState } from "react";
import { getCostSummary } from "../api";
import type { CostSummary } from "../types";

function errorMessage(err: unknown): string {
  return err instanceof Error ? err.message : "Something went wrong.";
}

function formatCost(value: number): string {
  return `$${value.toFixed(2)}`;
}

export function UsageCostPage() {
  const [summary, setSummary] = useState<CostSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setSummary(await getCostSummary());
    } catch (err) {
      setError(errorMessage(err));
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const isAdmin = summary?.users != null;

  return (
    <div>
      <p className="page-subtitle">
        Estimated LLM cost from tokens used during extraction, priced per the rates configured on
        the backend — not a live billing feed.
      </p>

      {summary == null && error == null && <p className="page-subtitle">Loading…</p>}

      {error && (
        <div className="error-banner">
          <span>{error}</span>
          <button onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}

      {summary && (
        <>
          <div className="stat-grid stat-grid--top">
            <div className="stat-card">
              <span className="stat-label">
                {isAdmin ? "Total Infrastructure Cost" : "Your Total Cost"}
              </span>
              <span className="stat-value">{formatCost(summary.overall_total_cost)}</span>
            </div>
          </div>

          <h3>Cost by project</h3>
          <table className="queue-table">
            <thead>
              <tr>
                <th>Project</th>
                <th>Documents</th>
                <th>Cost</th>
              </tr>
            </thead>
            <tbody>
              {summary.projects.map((p) => (
                <tr key={p.project_id}>
                  <td>{p.project_name}</td>
                  <td>{p.document_count}</td>
                  <td>{formatCost(p.total_cost)}</td>
                </tr>
              ))}
              {summary.projects.length === 0 && (
                <tr>
                  <td colSpan={3} className="page-subtitle">
                    No projects yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>

          {summary.users && (
            <>
              <h3>Cost by user</h3>
              <table className="queue-table">
                <thead>
                  <tr>
                    <th>User</th>
                    <th>Projects</th>
                    <th>Cost</th>
                  </tr>
                </thead>
                <tbody>
                  {summary.users.map((u) => (
                    <tr key={u.user_id ?? "orphaned"}>
                      <td>{u.email}</td>
                      <td>{u.project_count}</td>
                      <td>{formatCost(u.total_cost)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </>
      )}
    </div>
  );
}
