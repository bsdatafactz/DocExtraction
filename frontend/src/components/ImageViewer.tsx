import { useState } from "react";

interface Props {
  fileUrl: string;
  filename: string;
}

export function ImageViewer({ fileUrl, filename }: Props) {
  const [error, setError] = useState(false);
  const [loaded, setLoaded] = useState(false);

  if (error) {
    return <p className="pdf-viewer-error">Couldn't load this image.</p>;
  }

  return (
    <>
      {!loaded && <p className="pdf-viewer-loading">Loading document…</p>}
      <img
        className="image-viewer"
        style={loaded ? undefined : { display: "none" }}
        src={fileUrl}
        alt={filename}
        onLoad={() => setLoaded(true)}
        onError={() => setError(true)}
      />
    </>
  );
}
