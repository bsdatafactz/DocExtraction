import { useState } from "react";
import { deleteDocument } from "../api";
import type { DocumentSummary } from "../types";
import { ConfirmDialog } from "./ConfirmDialog";
import { StatusBadge } from "./StatusBadge";

interface Props {
  documents: DocumentSummary[];
  onSelect: (id: number) => void;
  onDeleted: () => void;
  onError: (err: unknown) => void;
  loadingDocumentId: number | null;
}

export function Queue({ documents, onSelect, onDeleted, onError, loadingDocumentId }: Props) {
  const [pendingDelete, setPendingDelete] = useState<DocumentSummary | null>(null);

  async function confirmDelete() {
    if (!pendingDelete) return;
    try {
      await deleteDocument(pendingDelete.id);
      onDeleted();
    } catch (err) {
      onError(err);
    } finally {
      setPendingDelete(null);
    }
  }

  if (documents.length === 0) {
    return <p className="queue-empty">No documents yet — upload one to get started.</p>;
  }

  return (
    <>
      <table className="queue-table">
        <thead>
          <tr>
            <th>Filename</th>
            <th>Status</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {documents.map((doc) => (
            <tr key={doc.id}>
              <td>{doc.filename}</td>
              <td>
                <StatusBadge status={doc.status} />
              </td>
              <td className="queue-actions">
                <button disabled={loadingDocumentId === doc.id} onClick={() => onSelect(doc.id)}>
                  {loadingDocumentId === doc.id ? "Loading…" : "Review"}
                </button>
                <button className="btn-danger" onClick={() => setPendingDelete(doc)}>
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {pendingDelete && (
        <ConfirmDialog
          message={`Delete ${pendingDelete.filename}? This can't be undone.`}
          onConfirm={confirmDelete}
          onCancel={() => setPendingDelete(null)}
        />
      )}
    </>
  );
}
