import { PdfViewer } from "./PdfViewer";

interface Props {
  fileUrl: string;
  filename: string;
}

const IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".tif", ".tiff"];

export function DocumentViewer({ fileUrl, filename }: Props) {
  const lower = filename.toLowerCase();

  if (lower.endsWith(".pdf")) {
    return <PdfViewer fileUrl={fileUrl} />;
  }

  if (IMAGE_EXTENSIONS.some((ext) => lower.endsWith(ext))) {
    return <img className="image-viewer" src={fileUrl} alt={filename} />;
  }

  return (
    <p className="pdf-viewer-error">
      No preview available for this file type. <a href={fileUrl}>Open it directly</a>.
    </p>
  );
}
