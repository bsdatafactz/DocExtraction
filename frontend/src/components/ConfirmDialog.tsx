interface Props {
  message: string;
  confirmLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
}

// Replaces window.confirm() — that's a browser-native dialog that shows the
// page's own origin ("localhost:5174 says...") and can't be styled, which
// reads as unfinished in an otherwise custom UI.
export function ConfirmDialog({ message, confirmLabel = "Delete", onConfirm, onCancel }: Props) {
  return (
    <div className="project-create-overlay" onClick={onCancel}>
      <div className="project-create-modal confirm-dialog" onClick={(e) => e.stopPropagation()}>
        <p>{message}</p>
        <div className="review-actions">
          <button className="btn" onClick={onCancel}>
            Cancel
          </button>
          <button className="btn btn-danger-solid" onClick={onConfirm}>
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
