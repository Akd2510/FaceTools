import React from "react";

/* ── Button ──────────────────────────────────────────────── */
export function Button({
  children,
  variant = "primary",
  size = "md",
  disabled,
  onClick,
  className = "",
  ...rest
}) {
  const base = {
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "0.6rem",
    border: "none",
    cursor: disabled ? "not-allowed" : "pointer",
    fontFamily: "var(--font-main)",
    fontWeight: 600,
    letterSpacing: "0.01em",
    transition: "var(--transition)",
    borderRadius: "var(--radius-md)",
    opacity: disabled ? 0.4 : 1,
    outline: "none",
    position: "relative",
    overflow: "hidden",
  };

  const sizes = {
    sm: { padding: "0.4rem 0.9rem", fontSize: "0.75rem" },
    md: { padding: "0.65rem 1.4rem", fontSize: "0.82rem" },
    lg: { padding: "0.9rem 2rem", fontSize: "0.95rem" },
  };

  const variants = {
    primary: {
      background: "linear-gradient(135deg, var(--cyan) 0%, #00b8d4 100%)",
      color: "#06070a",
      boxShadow: "0 4px 15px rgba(0, 229, 255, 0.3)",
    },
    ghost: {
      background: "rgba(255, 255, 255, 0.03)",
      color: "var(--cyan)",
      border: "1px solid rgba(0, 229, 255, 0.3)",
    },
    danger: {
      background: "rgba(255, 68, 68, 0.05)",
      color: "var(--red)",
      border: "1px solid rgba(255, 68, 68, 0.3)",
    },
    subtle: {
      background: "var(--bg-border)",
      color: "var(--text-secondary)",
      border: "1px solid transparent",
    },
  };

  return (
    <button
      style={{ ...base, ...sizes[size], ...variants[variant] }}
      disabled={disabled}
      onClick={onClick}
      className={`btn-hover-effect ${className}`}
      {...rest}
    >
      {children}
    </button>
  );
}

/* ── Badge ───────────────────────────────────────────────── */
export function Badge({ children, color = "cyan", dot = false }) {
  const colors = {
    cyan: {
      bg: "rgba(0, 229, 255, 0.08)",
      text: "var(--cyan)",
      border: "rgba(0, 229, 255, 0.2)",
    },
    green: {
      bg: "rgba(0, 255, 157, 0.08)",
      text: "var(--green)",
      border: "rgba(0, 255, 157, 0.2)",
    },
    amber: {
      bg: "rgba(255, 179, 0, 0.08)",
      text: "var(--amber)",
      border: "rgba(255, 179, 0, 0.2)",
    },
    red: {
      bg: "rgba(255, 68, 68, 0.08)",
      text: "var(--red)",
      border: "rgba(255, 68, 68, 0.2)",
    },
    muted: {
      bg: "rgba(255, 255, 255, 0.04)",
      text: "var(--text-secondary)",
      border: "var(--bg-border-light)",
    },
  };
  const c = colors[color] || colors.muted;
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "0.4rem",
        padding: "0.2rem 0.6rem",
        borderRadius: "20px",
        fontSize: "0.65rem",
        fontWeight: 700,
        letterSpacing: "0.04em",
        background: c.bg,
        color: c.text,
        border: `1px solid ${c.border}`,
        fontFamily: "var(--font-mono)",
        textTransform: "uppercase",
      }}
    >
      {dot && (
        <span
          style={{
            width: 4,
            height: 4,
            borderRadius: "50%",
            background: c.text,
            boxShadow: `0 0 6px ${c.text}`,
          }}
        />
      )}
      {children}
    </span>
  );
}

/* ── Status Badge ────────────────────────────────────────── */
export function StatusBadge({ status }) {
  const map = {
    done: { label: "Verified", color: "green" },
    processing: { label: "Analyzing", color: "cyan" },
    pending: { label: "In Queue", color: "amber" },
    failed: { label: "Failed", color: "red" },
  };
  const cfg = map[status] || { label: status.toUpperCase(), color: "muted" };
  return (
    <Badge color={cfg.color} dot={status === "processing"}>
      {cfg.label}
    </Badge>
  );
}

/* ── Card ────────────────────────────────────────────────── */
export function Card({ children, style = {}, className = "", glass = true }) {
  return (
    <div
      className={`${glass ? "glass-card" : ""} ${className}`}
      style={{
        borderRadius: "var(--radius-lg)",
        padding: "1.5rem",
        ...style,
      }}
    >
      {children}
    </div>
  );
}

/* ── Spinner ─────────────────────────────────────────────── */
export function Spinner({ size = 20, color = "var(--cyan)" }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      style={{ animation: "spin 1s cubic-bezier(0.4, 0, 0.2, 1) infinite" }}
    >
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      <circle
        cx="12"
        cy="12"
        r="10"
        stroke="rgba(255,255,255,0.1)"
        strokeWidth="3"
      />
      <circle
        cx="12"
        cy="12"
        r="10"
        stroke={color}
        strokeWidth="3"
        strokeDasharray="30 60"
        strokeLinecap="round"
      />
    </svg>
  );
}

/* ── Empty State ─────────────────────────────────────────── */
export function EmptyState({ icon, title, description }) {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: "1rem",
        padding: "4rem 2rem",
        color: "var(--text-muted)",
        textAlign: "center",
        background: "rgba(255,255,255,0.01)",
        borderRadius: "var(--radius-lg)",
        border: "1px dashed var(--bg-border)",
      }}
    >
      <div style={{ fontSize: "3rem", filter: "grayscale(1) opacity(0.5)" }}>
        {icon}
      </div>
      <div>
        <div
          style={{
            fontFamily: "var(--font-display)",
            fontWeight: 700,
            fontSize: "1.1rem",
            color: "var(--text-secondary)",
            marginBottom: "0.4rem",
          }}
        >
          {title}
        </div>
        {description && (
          <div
            style={{
              fontSize: "0.85rem",
              maxWidth: 400,
              margin: "0 auto",
              color: "var(--text-muted)",
            }}
          >
            {description}
          </div>
        )}
      </div>
    </div>
  );
}

/* ── Image Thumbnail ─────────────────────────────────────── */
export function Thumb({ src, alt = "", size = 56, style = {} }) {
  const [err, setErr] = React.useState(false);
  if (!src || err) {
    return (
      <div
        style={{
          width: size,
          height: size,
          borderRadius: "var(--radius-md)",
          background: "var(--bg-elevated)",
          border: "1px solid var(--bg-border)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "var(--text-muted)",
          fontSize: size * 0.3,
          flexShrink: 0,
          ...style,
        }}
      >
        NO IMG
      </div>
    );
  }
  return (
    <div
      style={{
        width: size,
        height: size,
        borderRadius: "var(--radius-md)",
        overflow: "hidden",
        border: "1px solid var(--bg-border-light)",
        background: "#000",
        flexShrink: 0,
        ...style,
      }}
    >
      <img
        src={src}
        alt={alt}
        onError={() => setErr(true)}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          transition: "transform 0.3s ease",
        }}
        onMouseEnter={(e) => (e.currentTarget.style.transform = "scale(1.1)")}
        onMouseLeave={(e) => (e.currentTarget.style.transform = "scale(1)")}
      />
    </div>
  );
}

/* ── Section Header ──────────────────────────────────────── */
export function SectionHeader({ title, subtitle, actions }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        marginBottom: "2.5rem",
      }}
    >
      <div>
        <h2
          style={{
            fontFamily: "var(--font-display)",
            fontWeight: 700,
            fontSize: "2.2rem",
            color: "var(--text-primary)",
            lineHeight: 1.1,
            letterSpacing: "-0.03em",
          }}
        >
          {title}
        </h2>
        {subtitle && (
          <p
            style={{
              fontSize: "0.9rem",
              color: "var(--text-secondary)",
              marginTop: "0.5rem",
              fontWeight: 400,
            }}
          >
            {subtitle}
          </p>
        )}
      </div>
      {actions && (
        <div style={{ display: "flex", gap: "0.75rem" }}>{actions}</div>
      )}
    </div>
  );
}
