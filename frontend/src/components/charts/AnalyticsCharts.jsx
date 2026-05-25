import React from "react";
import { Line, LineChart, PolarAngleAxis, PolarGrid, Radar, RadarChart, ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid, BarChart, Bar, Legend } from "recharts";

export function EEGLineChart({ data }) {
  return (
    <div className="chart-box">
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={data}>
          <CartesianGrid stroke="rgba(255,255,255,0.08)" />
          <XAxis dataKey="tick" hide />
          <YAxis stroke="#89a5d2" />
          <Tooltip contentStyle={{ background: "#0e1326", border: "1px solid #2d4e89", borderRadius: 10 }} />
          <Line type="monotone" dataKey="alpha" stroke="#22d3ee" dot={false} strokeWidth={2} />
          <Line type="monotone" dataKey="beta" stroke="#60a5fa" dot={false} strokeWidth={2} />
          <Line type="monotone" dataKey="theta" stroke="#a78bfa" dot={false} strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export function SessionRadar({ before, after }) {
  const data = [
    { metric: "Focus", before: before.focus, after: after.focus },
    { metric: "Relax", before: before.relaxation, after: after.relaxation },
    { metric: "Stability", before: before.stability, after: after.stability },
    { metric: "Sleep", before: before.sleep, after: after.sleep },
  ];

  return (
    <div className="chart-box">
      <ResponsiveContainer width="100%" height={260}>
        <RadarChart data={data}>
          <PolarGrid stroke="rgba(255,255,255,0.15)" />
          <PolarAngleAxis dataKey="metric" stroke="#97a9ce" />
          <Radar name="Before" dataKey="before" fill="#3b82f6" fillOpacity={0.25} stroke="#3b82f6" />
          <Radar name="After" dataKey="after" fill="#22d3ee" fillOpacity={0.3} stroke="#22d3ee" />
          <Legend />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function ImprovementBars({ before, after }) {
  const data = [
    { name: "Focus", before: before.focus, after: after.focus },
    { name: "Stress", before: before.stress, after: after.stress },
    { name: "Relax", before: before.relaxation, after: after.relaxation },
  ];

  return (
    <div className="chart-box">
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
          <XAxis dataKey="name" stroke="#89a5d2" />
          <YAxis stroke="#89a5d2" />
          <Tooltip contentStyle={{ background: "#0e1326", border: "1px solid #2d4e89", borderRadius: 10 }} />
          <Bar dataKey="before" fill="#64748b" radius={[6, 6, 0, 0]} />
          <Bar dataKey="after" fill="#22d3ee" radius={[6, 6, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
