import { useState } from "react";
import { createProject, deleteProject } from "../api";
import { DOCUMENT_TYPES } from "../constants";
import type { DocumentType, Project } from "../types";
import { ConfirmDialog } from "./ConfirmDialog";

interface Props {
  projects: Project[];
  onSelect: (project: Project) => void;
  onCreated: () => void;
  onError: (err: unknown) => void;
}

export function ProjectList({ projects, onSelect, onCreated, onError }: Props) {
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState("");
  const [documentType, setDocumentType] = useState<DocumentType>("invoice");
  const [submitting, setSubmitting] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [pendingDelete, setPendingDelete] = useState<Project | null>(null);

  async function handleCreate() {
    if (!name.trim()) return;
    setSubmitting(true);
    try {
      await createProject(name.trim(), documentType);
      setName("");
      setCreating(false);
      onCreated();
    } catch (err) {
      onError(err);
    } finally {
      setSubmitting(false);
    }
  }

  async function confirmDelete() {
    if (!pendingDelete) return;
    setDeletingId(pendingDelete.id);
    try {
      await deleteProject(pendingDelete.id);
      onCreated();
    } catch (err) {
      onError(err);
    } finally {
      setDeletingId(null);
      setPendingDelete(null);
    }
  }

  return (
    <div>
      <div className="project-grid">
        {projects.map((project) => (
          <div
            key={project.id}
            className="project-card"
            role="button"
            tabIndex={0}
            onClick={() => onSelect(project)}
            onKeyDown={(e) => e.key === "Enter" && onSelect(project)}
          >
            <div className="project-card-top">
              <span className={`badge badge-doctype-${project.document_type}`}>
                {DOCUMENT_TYPES.find((t) => t.value === project.document_type)?.label ??
                  project.document_type}
              </span>
              <button
                className="project-card-delete"
                disabled={deletingId === project.id}
                onClick={(e) => {
                  e.stopPropagation();
                  setPendingDelete(project);
                }}
                title="Delete project"
              >
                {deletingId === project.id ? "…" : "×"}
              </button>
            </div>
            <h3>{project.name}</h3>
            <span className="project-card-meta">
              {new Date(project.created_at).toLocaleDateString()}
            </span>
          </div>
        ))}

        <button className="project-card project-card--new" onClick={() => setCreating(true)}>
          <span className="project-card-plus">+</span>
          <span>New project</span>
        </button>
      </div>

      {creating && (
        <div className="project-create-overlay" onClick={() => setCreating(false)}>
          <div className="project-create-modal" onClick={(e) => e.stopPropagation()}>
            <h3>Create project</h3>
            <label>
              <span className="field-name">Project name</span>
              <input
                autoFocus
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Q3 Vendor Invoices"
              />
            </label>

            <span className="field-name">Document type</span>
            <div className="doctype-options">
              {DOCUMENT_TYPES.map((t) => (
                <button
                  key={t.value}
                  className={`doctype-option ${documentType === t.value ? "doctype-option--selected" : ""}`}
                  disabled={!t.implemented}
                  onClick={() => setDocumentType(t.value)}
                  title={t.implemented ? "" : "Coming soon — not yet implemented"}
                >
                  {t.label}
                  {!t.implemented && <span className="doctype-soon">Coming soon</span>}
                </button>
              ))}
            </div>

            <div className="review-actions">
              <button className="btn" onClick={() => setCreating(false)}>
                Cancel
              </button>
              <button
                className="btn btn-primary"
                disabled={submitting || !name.trim()}
                onClick={handleCreate}
              >
                {submitting ? "Creating…" : "Create project"}
              </button>
            </div>
          </div>
        </div>
      )}

      {pendingDelete && (
        <ConfirmDialog
          message={`Delete project "${pendingDelete.name}" and all its documents? This can't be undone.`}
          onConfirm={confirmDelete}
          onCancel={() => setPendingDelete(null)}
        />
      )}
    </div>
  );
}
