import { useState, useRef, useCallback } from "react";
import "./UploadZone.css";

export default function UploadZone({ onFile }) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef(null);

  const handleDrop = useCallback(
    (e) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files?.[0];
      if (file && file.type === "application/pdf") onFile(file);
    },
    [onFile]
  );

  const handleChange = useCallback(
    (e) => {
      const file = e.target.files?.[0];
      if (file) onFile(file);
    },
    [onFile]
  );

  return (
    <div className="upload-outer">
      <div className="upload-kicker">Step 01 — Document Intake</div>
      <h1 className="upload-headline">
        Drop a contract.<br />Get a structured profile.
      </h1>
      <p className="upload-sub">
        Powered by Atticus RoBERTa-base (CUAD) + Gemini 1.5 Flash.<br />
        Extracts parties, dates, obligations, and risk flags in seconds.
      </p>

      <div
        className={`drop-zone ${dragging ? "dragging" : ""}`}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
        aria-label="Upload PDF contract"
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf"
          onChange={handleChange}
          style={{ display: "none" }}
        />

        <div className="drop-icon">
          <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
            <rect x="8" y="4" width="24" height="32" rx="3" stroke="currentColor" strokeWidth="1.5" />
            <path d="M14 14h12M14 20h12M14 26h8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            <path d="M24 4v8h8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>

        <div className="drop-label">
          {dragging ? "Release to analyse" : "Drag & drop PDF here"}
        </div>
        <div className="drop-or">or</div>
        <div className="drop-browse">Click to browse</div>
      </div>

      <div className="upload-fields-preview">
        {[
          "Party Names",
          "Effective Date",
          "Expiration Date",
          "Renewal Terms",
          "Payment Terms",
          "Governing Law",
          "Termination",
          "Penalties",
        ].map((f) => (
          <span key={f} className="field-chip">{f}</span>
        ))}
      </div>
    </div>
  );
}
