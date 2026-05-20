import React, { useEffect, useState } from "react";
import { fetchStats } from "../utils/api";
import { Card } from "./UI";

function StatItem({ label, value, color = "var(--text-primary)", icon }) {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "0.4rem",
        padding: "0.5rem 1rem",
        flex: 1,
        minWidth: "140px",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
        <span
          style={{
            fontSize: "0.62rem",
            color: "var(--text-muted)",
            letterSpacing: "0.12em",
            fontWeight: 800,
            textTransform: "uppercase",
          }}
        >
          {label}
        </span>
      </div>
      <div style={{ display: "flex", alignItems: "baseline", gap: "0.4rem" }}>
        <span
          style={{
            fontSize: "1.8rem",
            fontWeight: 800,
            color,
            fontFamily: "var(--font-display)",
            lineHeight: 1,
            textShadow: `0 0 20px ${color}33`,
          }}
        >
          {value ?? "0"}
        </span>
        {icon && (
          <span
            style={{
              color: "var(--text-muted)",
              fontSize: "0.8rem",
              opacity: 0.5,
            }}
          >
            {icon}
          </span>
        )}
      </div>
    </div>
  );
}

export default function StatsBar() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    const load = () =>
      fetchStats()
        .then((r) => setStats(r.data))
        .catch(() => {});
    load();
    const id = setInterval(load, 8000);
    return () => clearInterval(id);
  }, []);

  return (
    <Card
      style={{
        display: "flex",
        alignItems: "center",
        flexWrap: "wrap",
        gap: "1rem",
        marginBottom: "2.5rem",
        padding: "1.25rem 1.5rem",
        background: "rgba(255,255,255,0.02)",
        border: "1px solid var(--bg-border-light)",
      }}
    >
      <StatItem
        label="Detections"
        value={stats?.total_faces}
        color="var(--cyan)"
      />
      <div
        style={{
          width: 1,
          height: 30,
          background: "var(--bg-border)",
          opacity: 0.5,
        }}
      />
      <StatItem
        label="Clusters"
        value={stats?.total_clusters}
        color="var(--violet)"
      />
      <div
        style={{
          width: 1,
          height: 30,
          background: "var(--bg-border)",
          opacity: 0.5,
        }}
      />
      <StatItem
        label="Total Pool"
        value={stats?.total_images}
        color="var(--text-primary)"
      />
      <div
        style={{
          width: 1,
          height: 30,
          background: "var(--bg-border)",
          opacity: 0.5,
        }}
      />
      <StatItem
        label="Processed"
        value={stats?.processed}
        color="var(--green)"
      />
      <div
        style={{
          width: 1,
          height: 30,
          background: "var(--bg-border)",
          opacity: 0.5,
        }}
      />
      <StatItem label="Queue" value={stats?.pending} color="var(--amber)" />
      <div
        style={{
          width: 1,
          height: 30,
          background: "var(--bg-border)",
          opacity: 0.5,
        }}
      />
      <StatItem label="Error Log" value={stats?.failed} color="var(--red)" />
    </Card>
  );
}
