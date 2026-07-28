import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { listDocuments } from "../api";
import { useAuth } from "../AuthContext";
import { Queue } from "../components/Queue";
import { UploadDropzone } from "../components/UploadDropzone";
import type { DocumentSummary } from "../types";

const POLL_INTERVAL_MS = 4000;

function errorMessage(err: unknown): string {
  return err instanceof Error ? err.message : "Something went wrong.";
}

export function UploadPage() {
  const { projectId } = useParams();
  const id = Number(projectId);
  const { user } = useAuth();
  const navigate = useNavigate();
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setDocuments(await listDocuments(id));
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
      {error && (
        <div className="error-banner">
          <span>{error}</span>
          <button onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}
      <UploadDropzone
        projectId={id}
        onUploaded={refresh}
        onError={(err) => setError(`Upload failed: ${errorMessage(err)}`)}
      />
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
