import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { getDocument } from "../api";
import { useAuth } from "../AuthContext";
import { ReviewScreen } from "../components/ReviewScreen";
import type { DocumentDetail } from "../types";

function errorMessage(err: unknown): string {
  return err instanceof Error ? err.message : "Something went wrong.";
}

export function DocumentDetailPage() {
  const { documentId } = useParams();
  const id = Number(documentId);
  const { user } = useAuth();
  const navigate = useNavigate();
  const [document, setDocument] = useState<DocumentDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setDocument(await getDocument(id));
    } catch (err) {
      setError(errorMessage(err));
    }
  }, [id]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return (
    <div>
      <button className="back-link" onClick={() => navigate(-1)}>
        ← Back
      </button>

      {error && (
        <div className="error-banner">
          <span>{error}</span>
          <button onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}

      {document && (
        <ReviewScreen
          document={document}
          onDone={() => navigate(-1)}
          onError={(err) => setError(errorMessage(err))}
          isAdmin={user?.role === "admin"}
        />
      )}
    </div>
  );
}
