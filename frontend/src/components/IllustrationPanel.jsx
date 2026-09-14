// Panel decorativo del layout de autenticación de dos columnas.
// "network": panel oscuro con globo/nodos, como Sign In / Crear cuenta.
// "chat": ilustración clara de conversación, como verificación / restablecer contraseña.
// "success": variante oscura con check, para la pantalla de éxito.
export default function IllustrationPanel({ variant = "network" }) {
  if (variant === "chat") {
    return (
      <div className="illustration illustration--light">
        <svg viewBox="0 0 320 320" width="70%" role="presentation">
          <circle cx="160" cy="150" r="120" fill="#E9ECFB" />
          <circle cx="95" cy="150" r="44" fill="#F5A623" />
          <circle cx="230" cy="160" r="52" fill="#2D3F82" />
          <rect x="120" y="70" width="130" height="80" rx="18" fill="#ffffff" stroke="#C7CDE6" strokeWidth="2" />
          <circle cx="145" cy="108" r="6" fill="#2D3F82" />
          <circle cx="170" cy="108" r="6" fill="#2D3F82" />
          <circle cx="195" cy="108" r="6" fill="#2D3F82" />
          <path d="M150 150 L135 172 L175 150 Z" fill="#ffffff" stroke="#C7CDE6" strokeWidth="2" />
          <rect x="70" y="190" width="60" height="90" rx="14" fill="#0F1A3D" />
          <circle cx="100" cy="205" r="14" fill="#F2C79A" />
          <rect x="180" y="180" width="66" height="100" rx="14" fill="#2D3F82" />
          <circle cx="213" cy="196" r="15" fill="#F2C79A" />
        </svg>
      </div>
    );
  }

  if (variant === "success") {
    return (
      <div className="illustration illustration--dark">
        <svg viewBox="0 0 220 220" width="55%" role="presentation">
          <circle cx="110" cy="110" r="100" fill="rgba(245,166,35,0.12)" />
          <circle cx="110" cy="110" r="72" fill="rgba(245,166,35,0.2)" />
          <circle cx="110" cy="110" r="46" fill="#F5A623" />
          <path
            d="M92 111 L104 124 L130 96"
            stroke="#0F1A3D"
            strokeWidth="8"
            strokeLinecap="round"
            strokeLinejoin="round"
            fill="none"
          />
        </svg>
      </div>
    );
  }

  return (
    <div className="illustration illustration--dark">
      <svg viewBox="0 0 320 320" width="80%" role="presentation">
        <circle cx="160" cy="160" r="118" fill="none" stroke="rgba(245,166,35,0.35)" strokeWidth="1.5" />
        <circle cx="160" cy="160" r="86" fill="none" stroke="rgba(245,166,35,0.25)" strokeWidth="1.5" />
        <circle cx="160" cy="160" r="52" fill="#F5A623" opacity="0.9" />
        {[
          [60, 90], [250, 70], [270, 190], [90, 250], [200, 260], [50, 180], [230, 40],
        ].map(([cx, cy], i) => (
          <circle key={i} cx={cx} cy={cy} r={5} fill="#F5A623" opacity={0.85} />
        ))}
        <path
          d="M60 90 L160 160 L250 70 M270 190 L160 160 L90 250 M200 260 L160 160 L50 180 M230 40 L160 160"
          stroke="rgba(245,166,35,0.45)"
          strokeWidth="1.2"
          fill="none"
        />
      </svg>
    </div>
  );
}
