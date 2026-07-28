import { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { uploadDocument } from "../api";

interface Props {
  projectId: number;
  onUploaded: () => void;
  onError: (err: unknown) => void;
}

export function UploadDropzone({ projectId, onUploaded, onError }: Props) {
  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      try {
        await Promise.all(acceptedFiles.map((file) => uploadDocument(projectId, file)));
        onUploaded();
      } catch (err) {
        onError(err);
      }
    },
    [projectId, onUploaded, onError],
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"], "image/*": [".png", ".jpg", ".jpeg", ".tiff"] },
  });

  return (
    <div {...getRootProps()} className={`dropzone ${isDragActive ? "dropzone--active" : ""}`}>
      <input {...getInputProps()} />
      <svg
        className="dropzone-icon"
        width="28"
        height="28"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.6"
      >
        <path
          d="M12 15V4M12 4l-4 4M12 4l4 4M5 16v2a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      <p>
        Drag and drop invoices here, or click to browse
        <span className="dropzone-hint">PDF, PNG, JPG, TIFF</span>
      </p>
    </div>
  );
}
