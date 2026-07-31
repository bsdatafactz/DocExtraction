import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { listProjects } from "../api";
import { ProjectList } from "../components/ProjectList";
import type { Project } from "../types";

function errorMessage(err: unknown): string {
  return err instanceof Error ? err.message : "Something went wrong.";
}

export function ProjectsPage() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Project[]>([]);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setProjects(await listProjects());
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
      <ProjectList
        projects={projects}
        onSelect={(p) => navigate(`/projects/${p.id}/upload`)}
        onCreated={refresh}
        onError={(err) => setError(errorMessage(err))}
      />
    </div>
  );
}
