import { useState, useCallback } from "react";
import UploadZone from "./components/UploadZone";
import ProcessingState from "./components/ProcessingState";
import ContractProfile from "./components/ContractProfile";
import "./App.css";

const API_BASE = "";

export default function App() {
  const [phase, setPhase] = useState("idle");
  const [profile, setProfile] = useState(null);
  const [errorMsg, setErrorMsg] = useState("");
  const [fileName, setFileName] = useState("");

  const handleFile = useCallback(async (file) => {
    setFileName(file.name);
    setPhase("processing");
    setProfile(null);
    setErrorMsg("");

    const form = new FormData();
    form.append("file", file);
    form.append("mode", "hybrid"); // fixed — no user choice

    try {
      const res = await fetch(`${API_BASE}/extract`, { method: "POST", body: form });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Server error ${res.status}`);
      }
      const data = await res.json();
      setProfile(data);
      setPhase("done");
    } catch (err) {
      setErrorMsg(err.message || "Unknown error");
      setPhase("error");
    }
  }, []);

  const reset = () => {
    setPhase("idle");
    setProfile(null);
    setErrorMsg("");
    setFileName("");
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-left">
          <span className="header-tag">NLP·LAB</span>
          <span className="header-title">Contract Extractor</span>
        </div>
        <div className="header-right">
          {phase === "done" && (
            <button className="reset-btn" onClick={reset}>
              ← New Contract
            </button>
          )}
          <div className="model-badge">
            <span className="badge-dot roberta" />
            RoBERTa-base
            <span className="badge-dot gemini" />
            Gemini 2.5
          </div>
        </div>
      </header>

      <main className="app-main">
        {phase === "idle" && (
          <div className="idle-wrap">
            <div className="routing-info">
              Optimised model routing — RoBERTa for dates &amp; law · Gemini for parties &amp; clauses
            </div>
            <UploadZone onFile={handleFile} />
          </div>
        )}
        {phase === "processing" && (
          <ProcessingState fileName={fileName} mode="hybrid" />
        )}
        {phase === "done" && profile && (
          <ContractProfile data={profile} fileName={fileName} />
        )}
        {phase === "error" && (
          <div className="error-card">
            <div className="error-icon">⚠</div>
            <div className="error-title">Extraction Failed</div>
            <div className="error-msg">{errorMsg}</div>
            <button className="reset-btn" onClick={reset} style={{ marginTop: 24 }}>
              Try Again
            </button>
          </div>
        )}
      </main>

      <footer className="app-footer">
        CUAD v1 · Atticus Project · Gemini 2.5 Flash · Contract Extractor
      </footer>
    </div>
  );
}
