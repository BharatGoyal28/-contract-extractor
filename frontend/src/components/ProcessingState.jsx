import { useEffect, useState } from "react";
import "./ProcessingState.css";

const STEPS_BY_MODE = {
  roberta: [
    { label: "Extracting PDF text", duration: 1500 },
    { label: "Loading RoBERTa-base (CUAD)", duration: 8000 },
    { label: "Running extractive QA — all 9 fields", duration: 12000 },
    { label: "Assembling contract profile", duration: 2000 },
  ],
  gemini: [
    { label: "Extracting PDF text", duration: 1500 },
    { label: "Calling Gemini — all 9 fields", duration: 20000 },
    { label: "Assembling contract profile", duration: 2000 },
  ],
  hybrid: [
    { label: "Extracting PDF text", duration: 1500 },
    { label: "Loading RoBERTa-base (CUAD)", duration: 8000 },
    { label: "Running extractive QA — dates & law", duration: 5000 },
    { label: "Calling Gemini — parties & clauses", duration: 12000 },
    { label: "Assembling contract profile", duration: 2000 },
  ],
};

export default function ProcessingState({ fileName, mode = "hybrid" }) {
  const [activeStep, setActiveStep] = useState(0);
  const [elapsed, setElapsed] = useState(0);

  const STEPS = STEPS_BY_MODE[mode] || STEPS_BY_MODE.hybrid;

  useEffect(() => {
    setActiveStep(0);
    const start = Date.now();
    const ticker = setInterval(() => setElapsed(Math.floor((Date.now() - start) / 1000)), 200);

    let cumulative = 0;
    const timers = STEPS.map((step, i) => {
      cumulative += step.duration;
      return setTimeout(() => setActiveStep((s) => Math.max(s, i + 1)), cumulative);
    });

    return () => {
      clearInterval(ticker);
      timers.forEach(clearTimeout);
    };
  }, [mode]);

  const totalDuration = STEPS.reduce((s, x) => s + x.duration, 0);
  const progress = Math.min(
    100,
    (STEPS.slice(0, activeStep).reduce((s, x) => s + x.duration, 0) / totalDuration) * 100
  );

  return (
    <div className="processing-outer">
      <div className="processing-card">
        <div className="proc-kicker">Analysing Contract</div>
        <div className="proc-filename">{fileName}</div>

        {/* Animated orb */}
        <div className="proc-orb-wrap">
          <div className="proc-orb">
            <div className="orb-ring r1" />
            <div className="orb-ring r2" />
            <div className="orb-ring r3" />
            <div className="orb-core" />
          </div>
        </div>

        {/* Progress bar */}
        <div className="proc-bar-track">
          <div className="proc-bar-fill" style={{ width: `${progress}%` }} />
        </div>
        <div className="proc-pct">{Math.round(progress)}%</div>

        {/* Steps */}
        <div className="proc-steps">
          {STEPS.map((step, i) => (
            <div
              key={i}
              className={`proc-step ${i < activeStep ? "done" : ""} ${i === activeStep ? "active" : ""}`}
            >
              <div className="step-dot" />
              <span>{step.label}</span>
            </div>
          ))}
        </div>

        <div className="proc-elapsed">
          {elapsed}s elapsed · mode: {mode}
        </div>
      </div>
    </div>
  );
}
