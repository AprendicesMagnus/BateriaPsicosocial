import IllustrationPanel from "./IllustrationPanel";
import "../styles/auth.css";

export default function AuthLayout({ illustration = "network", children }) {
  return (
    <div className="auth-shell">
      <div className="auth-card">
        <div className="auth-side">
          <IllustrationPanel variant={illustration} />
        </div>
        <div className="auth-form-panel">{children}</div>
      </div>
    </div>
  );
}
