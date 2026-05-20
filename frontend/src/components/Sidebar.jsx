import React from "react";
import { NavLink } from "react-router-dom";

const NAV = [
  { to: "/", label: "Dashboard", icon: "⬡", desc: "OVERVIEW" },
  { to: "/upload", label: "Upload", icon: "↑", desc: "ADD IMAGES" },
  { to: "/clusters", label: "Clusters", icon: "❖", desc: "GROUP FACES" },
  { to: "/search", label: "Search", icon: "⊙", desc: "FIND IDENTITY" },
  { to: "/faceswap", label: "FaceSwap", icon: "⇆", desc: "SWAP FACES" },
];

export default function Sidebar() {
  return (
    <aside
      style={{
        width: 260,
        minHeight: "100vh",
        flexShrink: 0,
        background: "rgba(10, 11, 15, 0.4)",
        backdropFilter: "blur(20px)",
        borderRight: "1px solid var(--bg-border-light)",
        display: "flex",
        flexDirection: "column",
        padding: "2.5rem 0",
        position: "sticky",
        top: 0,
        zIndex: 100,
      }}
    >
      {/* Branding */}
      <div style={{ padding: "0 2rem", marginBottom: "3.5rem" }}>
        <div
          style={{
            fontFamily: "var(--font-display)",
            fontWeight: 800,
            fontSize: "1.4rem",
            color: "var(--cyan)",
            letterSpacing: "-0.04em",
            display: "flex",
            alignItems: "center",
            gap: "0.4rem",
          }}
        >
          <div
            style={{
              width: 8,
              height: 24,
              background: "var(--cyan)",
              borderRadius: 2,
            }}
          />
          FACE<span style={{ color: "#fff" }}>TOOLS</span>
        </div>
        <div
          style={{
            fontSize: "0.65rem",
            color: "var(--text-muted)",
            marginTop: "0.3rem",
            letterSpacing: "0.1em",
            fontWeight: 700,
          }}
        >
          PREMIUM AI SUITE
        </div>
      </div>

      {/* Navigation */}
      <nav style={{ flex: 1 }}>
        {NAV.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            style={({ isActive }) => ({
              display: "flex",
              alignItems: "center",
              gap: "1rem",
              padding: "0.85rem 2rem",
              color: isActive ? "#fff" : "var(--text-secondary)",
              background: isActive
                ? "linear-gradient(90deg, rgba(0,229,255,0.08) 0%, transparent 100%)"
                : "transparent",
              borderLeft: isActive
                ? "3px solid var(--cyan)"
                : "3px solid transparent",
              textDecoration: "none",
              transition: "var(--transition)",
              position: "relative",
            })}
            className={({ isActive }) => (isActive ? "nav-active" : "")}
          >
            <span
              style={{
                fontSize: "1.2rem",
                opacity: 0.8,
                color: "inherit",
                width: "1.5rem",
                display: "inline-block",
                textAlign: "center",
              }}
            >
              {item.icon}
            </span>
            <div style={{ display: "flex", flexDirection: "column" }}>
              <span
                style={{
                  fontSize: "0.88rem",
                  fontWeight: 600,
                  letterSpacing: "0.01em",
                }}
              >
                {item.label}
              </span>
              <span
                style={{
                  fontSize: "0.58rem",
                  color: "var(--text-muted)",
                  letterSpacing: "0.05em",
                  fontWeight: 700,
                }}
              >
                {item.desc}
              </span>
            </div>

            {/* Active Indicator Glow */}
            <style>{`
              .nav-active::after {
                content: '';
                position: absolute;
                left: 0;
                top: 20%;
                height: 60%;
                width: 15px;
                background: var(--cyan);
                filter: blur(15px);
                opacity: 0.4;
                pointer-events: none;
              }
            `}</style>
          </NavLink>
        ))}
      </nav>

      {/* Footer info */}
      <div
        style={{
          padding: "1.5rem 2rem",
          borderTop: "1px solid var(--bg-border-light)",
          fontSize: "0.65rem",
          color: "var(--text-muted)",
          lineHeight: 2,
          fontWeight: 500,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <span
            style={{
              width: 4,
              height: 4,
              borderRadius: "50%",
              background: "var(--green)",
            }}
          />
          SYSTEM ENGINE ONLINE
        </div>
        <div style={{ marginTop: "0.5rem", opacity: 0.7 }}>V2.4.0-STABLE</div>
      </div>
    </aside>
  );
}
