import { ImageViewer } from "./ImageViewer";
import { PdfViewer } from "./PdfViewer";

interface Props {
  fileUrl: string;
  filename: string;
}

// TIFF is deliberately excluded — browsers can't decode it in an <img>, so
// it's better routed to the "no preview" fallback than shown as a silently
// broken image.
const IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png"];

export function DocumentViewer({ fileUrl, filename }: Props) {
  const lower = filename.toLowerCase();

  if (lower.endsWith(".pdf")) {
    return <PdfViewer fileUrl={fileUrl} />;
  }

  if (IMAGE_EXTENSIONS.some((ext) => lower.endsWith(ext))) {
    return <ImageViewer fileUrl={fileUrl} filename={filename} />;
  }

  return (
    <p className="pdf-viewer-error">
      No preview available for this file type. <a href={fileUrl}>Open it directly</a>.
    </p>
  );
}
