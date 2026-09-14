export default function Logo({ variant = "dark", size = 22 }) {
  const isLight = variant === "light";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <svg width={size + 10} height={size + 10} viewBox="0 0 40 40" fill="none">
        <rect width="40" height="40" rx="10" fill={isLight ? "#F5A623" : "#0F1A3D"} />
        <path
          d="M10 27V13l10 9 10-9v14"
          stroke={isLight ? "#0F1A3D" : "#F5A623"}
          strokeWidth="2.6"
          strokeLinecap="round"
          strokeLinejoin="round"
          fill="none"
        />
      </svg>
      <span
        style={{
          fontWeight: 800,
          fontSize: size,
          letterSpacing: 0.2,
          color: isLight ? "#ffffff" : "#0F1A3D",
        }}
      >
        MAGNUS<span style={{ color: "#F5A623" }}>|SIG</span>
      </span>
    </div>
  );
}
