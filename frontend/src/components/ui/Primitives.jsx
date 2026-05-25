import React from "react";
import { motion } from "framer-motion";

export function GlassCard({ title, children, className = "" }) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className={`glass-card ${className}`}
    >
      {title ? <p className="section-kicker">{title}</p> : null}
      {children}
    </motion.section>
  );
}

export function CTAButton({ children, onClick, disabled = false, kind = "primary" }) {
  return (
    <button className={`cta-btn ${kind}`} disabled={disabled} onClick={onClick}>
      {children}
    </button>
  );
}

export function ProgressBar({ label, value, color = "cyan" }) {
  return (
    <div className="metric-line">
      <div className="metric-head">
        <span>{label}</span>
        <span>{value}%</span>
      </div>
      <div className="metric-track">
        <div className={`metric-fill ${color}`} style={{ width: `${value}%` }} />
      </div>
    </div>
  );
}

export function CircularMeter({ value, label }) {
  const radius = 49;
  const circ = 2 * Math.PI * radius;
  const offset = circ - (value / 100) * circ;

  return (
    <div className="circular-meter">
      <svg viewBox="0 0 120 120">
        <circle className="c-bg" cx="60" cy="60" r={radius} />
        <circle className="c-fg" cx="60" cy="60" r={radius} style={{ strokeDasharray: circ, strokeDashoffset: offset }} />
      </svg>
      <div className="meter-content">
        <strong>{value}%</strong>
        <span>{label}</span>
      </div>
    </div>
  );
}

export function Skeleton({ className = "" }) {
  return <div className={`skeleton ${className}`} />;
}
