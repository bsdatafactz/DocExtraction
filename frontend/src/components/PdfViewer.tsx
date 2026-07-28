import { useEffect, useRef, useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import workerUrl from "pdfjs-dist/build/pdf.worker.min.mjs?url";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";

pdfjs.GlobalWorkerOptions.workerSrc = workerUrl;

interface Props {
  fileUrl: string;
}

// Fit every page to the container's actual width, not a fixed guess — a
// narrower review pane (smaller viewport, or the fields pane growing) should
// shrink the page in step, never trigger horizontal scroll.
export function PdfViewer({ fileUrl }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState<number>();
  const [numPages, setNumPages] = useState(0);
  const [error, setError] = useState(false);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const observer = new ResizeObserver(([entry]) => setWidth(entry.contentRect.width));
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <div ref={containerRef} className="pdf-viewer">
      {error && <p className="pdf-viewer-error">Couldn't load this document.</p>}
      {width != null && (
        <Document
          file={fileUrl}
          onLoadSuccess={({ numPages }) => setNumPages(numPages)}
          onLoadError={() => setError(true)}
          loading={<p className="pdf-viewer-loading">Loading document…</p>}
        >
          {Array.from({ length: numPages }, (_, i) => (
            <Page key={i} pageNumber={i + 1} width={width} />
          ))}
        </Document>
      )}
    </div>
  );
}
