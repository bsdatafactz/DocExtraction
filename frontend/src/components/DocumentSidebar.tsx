import type { DocumentSummary } from "../types";

interface Props {
  documents: DocumentSummary[];
  activeId: number;
  onSelect: (id: number) => void;
}

export function DocumentSidebar({ documents, activeId, onSelect }: Props) {
  return (
    <div className="document-sidebar">
      {documents.map((doc) => (
        <button
          key={doc.id}
          className={`document-sidebar-item ${doc.id === activeId ? "document-sidebar-item--active" : ""}`}
          onClick={() => onSelect(doc.id)}
        >
          <span className="document-sidebar-filename" title={doc.filename}>
            {doc.filename}
          </span>
        </button>
      ))}
      {documents.length === 0 && <p className="page-subtitle">No documents in this project.</p>}
    </div>
  );
}
