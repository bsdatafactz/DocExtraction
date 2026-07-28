import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { listDocuments } from "../api";
import { useAuth } from "../AuthContext";
import { Queue } from "../components/Queue";
import type { DocumentSummary } from "../types";

const POLL_INTERVAL_MS = 4000;

function errorMessage(err: unknown): string {
  return err instanceof Error ? err.message : "Something went wrong.";
}

export function ReviewQueuePage() {
  const { projectId } = useParams();
  const id = Number(projectId);
  const { user } = useAuth();
  const navigate = useNavigate();
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setDocuments(await listDocuments(id, "needs_review"));
    } catch (err) {
      setError(errorMessage(err));
    }
  }, [id]);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [refresh]);

  return (
    <div>
      <p className="page-subtitle">
        Documents below the 90% confidence threshold — everything else auto-approves without a
        manual step.
      </p>
      {error && (
        <div className="error-banner">
          <span>{error}</span>
          <button onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}
      <Queue
        documents={documents}
        onSelect={(docId) => navigate(`/documents/${docId}`)}
        onDeleted={refresh}
        onError={(err) => setError(errorMessage(err))}
        loadingDocumentId={null}
        isAdmin={user?.role === "admin"}
      />
    </div>
  );
}
