import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { getDocument, listDocuments } from "../api";
import { DocumentSidebar } from "../components/DocumentSidebar";
import { ReviewScreen } from "../components/ReviewScreen";
import type { DocumentDetail, DocumentSummary } from "../types";

function errorMessage(err: unknown): string {
  return err instanceof Error ? err.message : "Something went wrong.";
}

export function DocumentDetailPage() {
  const { projectId, documentId } = useParams();
  const id = Number(documentId);
  const navigate = useNavigate();
  const [document, setDocument] = useState<DocumentDetail | null>(null);
  const [siblings, setSiblings] = useState<DocumentSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const detail = await getDocument(id);
      setDocument(detail);
      setSiblings(await listDocuments(detail.project_id));
    } catch (err) {
      setError(errorMessage(err));
    }
  }, [id]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return (
    <div>
      <button className="back-link" onClick={() => navigate(`/projects/${projectId}/upload`)}>
        ← Back
      </button>

      {error && (
        <div className="error-banner">
          <span>{error}</span>
          <button onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}

      {document && (
        <div className="document-detail-layout">
          <DocumentSidebar
            documents={siblings}
            activeId={id}
            onSelect={(docId) =>
              navigate(`/projects/${document.project_id}/documents/${docId}`, { replace: true })
            }
          />
          <ReviewScreen
            document={document}
            onDone={() => {
              refresh();
              navigate(`/projects/${document.project_id}/upload`);
            }}
            onError={(err) => setError(errorMessage(err))}
          />
        </div>
      )}
    </div>
  );
}
