import "./ContractProfile.css";

/* ── Helpers ──────────────────────────────────────────────────────── */

function parseDate(str) {
  if (!str || str.toLowerCase().includes("not found")) return null;
  const d = new Date(str);
  return isNaN(d.getTime()) ? null : d;
}

function daysUntil(date) {
  if (!date) return null;
  return Math.ceil((date - new Date()) / (1000 * 60 * 60 * 24));
}

function deadlineFlag(days) {
  if (days === null) return null;
  if (days < 0)  return { label: "EXPIRED",       cls: "flag-expired" };
  if (days <= 30) return { label: `${days}d LEFT`, cls: "flag-red" };
  if (days <= 90) return { label: `${days}d LEFT`, cls: "flag-amber" };
  return null;
}

function ConfidenceBar({ score }) {
  const pct = Math.round(score * 100);
  const cls = pct >= 70 ? "conf-high" : pct >= 40 ? "conf-mid" : "conf-low";
  return (
    <div className="conf-wrap" title={`Confidence: ${pct}%`}>
      <div className={`conf-track ${cls}`}>
        <div className="conf-fill" style={{ width: `${pct}%` }} />
      </div>
      <span className="conf-label">{pct}%</span>
    </div>
  );
}

function SourceBadge({ source }) {
  const label = source?.startsWith("fallback") ? "fallback→Gemini"
    : source === "roberta" ? "RoBERTa"
    : source === "gemini" ? "Gemini"
    : source;
  const cls = source === "roberta" ? "src-roberta" : "src-gemini";
  return <span className={`src-badge ${cls}`}>{label}</span>;
}

function FieldRow({ label, field, dateFlag }) {
  const missing = !field?.value || field.value.toLowerCase().includes("not found");
  return (
    <div className={`field-row ${missing ? "field-missing" : ""}`}>
      <div className="field-meta">
        <span className="field-label">{label}</span>
        {!missing && <SourceBadge source={field.source} />}
      </div>
      <div className="field-value-row">
        <span className={`field-value ${missing ? "value-missing" : ""}`}>
          {missing ? "Not found in contract" : field.value}
        </span>
        {dateFlag && <span className={`deadline-flag ${dateFlag.cls}`}>{dateFlag.label}</span>}
      </div>
      {!missing && field.confidence > 0 && (
        <ConfidenceBar score={field.confidence} />
      )}
    </div>
  );
}

function Section({ title, icon, children }) {
  return (
    <div className="profile-section">
      <div className="section-header">
        <span className="section-icon">{icon}</span>
        <span className="section-title">{title}</span>
      </div>
      <div className="section-body">{children}</div>
    </div>
  );
}

/* ── Main component ───────────────────────────────────────────────── */

export default function ContractProfile({ data, fileName }) {
  const expDate = parseDate(data.expiration_date?.value);
  const expDays = daysUntil(expDate);
  const expFlag = deadlineFlag(expDays);

  const effDate = parseDate(data.effective_date?.value);
  const totalMs = data.total_latency_ms || 0;

  const fieldsExtracted = [
    data.party_1, data.party_2, data.effective_date, data.expiration_date,
    data.renewal, data.governing_law, data.termination_for_cause,
    data.payment_terms, data.penalties,
  ].filter((f) => f?.value && !f.value.toLowerCase().includes("not found")).length;

  return (
    <div className="profile-outer">
      {/* Top meta bar */}
      <div className="profile-topbar">
        <div className="profile-topbar-left">
          <div className="profile-filename">{fileName || "Contract"}</div>
          <div className="profile-meta-chips">
            <span className="meta-chip">{fieldsExtracted}/9 fields extracted</span>
            <span className="meta-chip">{(totalMs / 1000).toFixed(1)}s total</span>
            {expFlag && (
              <span className={`meta-chip deadline-chip ${expFlag.cls}`}>
                {expFlag.label}
              </span>
            )}
          </div>
        </div>
        <div className="profile-score-ring">
          <svg viewBox="0 0 64 64" width="64" height="64">
            <circle cx="32" cy="32" r="26" fill="none" stroke="var(--border)" strokeWidth="4" />
            <circle
              cx="32" cy="32" r="26"
              fill="none"
              stroke={fieldsExtracted >= 7 ? "var(--green)" : fieldsExtracted >= 4 ? "var(--amber)" : "var(--red)"}
              strokeWidth="4"
              strokeDasharray={`${(fieldsExtracted / 9) * 163.4} 163.4`}
              strokeLinecap="round"
              transform="rotate(-90 32 32)"
            />
          </svg>
          <span className="score-num">{Math.round((fieldsExtracted / 9) * 100)}%</span>
        </div>
      </div>

      {/* Sections */}
      <div className="profile-grid">

        <Section title="Parties" icon="⚖">
          <FieldRow label="Party 1" field={data.party_1} />
          <FieldRow label="Party 2" field={data.party_2} />
        </Section>

        <Section title="Key Dates" icon="📅">
          <FieldRow label="Effective Date" field={data.effective_date} />
          <FieldRow
            label="Expiration Date"
            field={data.expiration_date}
            dateFlag={expFlag}
          />
          <FieldRow label="Renewal Terms" field={data.renewal} />
        </Section>

        <Section title="Financial Terms" icon="$">
          <FieldRow label="Payment Terms" field={data.payment_terms} />
          <FieldRow label="Penalties & Damages" field={data.penalties} />
        </Section>

        <Section title="Legal Conditions" icon="§">
          <FieldRow label="Governing Law" field={data.governing_law} />
          <FieldRow label="Termination for Cause" field={data.termination_for_cause} />
        </Section>

      </div>

      {/* Raw JSON toggle */}
      <details className="raw-toggle">
        <summary>View raw JSON output</summary>
        <pre className="raw-json">{JSON.stringify(data, null, 2)}</pre>
      </details>
    </div>
  );
}
