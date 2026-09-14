import Logo from "./Logo";
import IllustrationPanel from "./IllustrationPanel";
import "../styles/auth.css";

export default function AuthLayout({ illustration = "network", children }) {
  const isDark = illustration !== "chat";
  return (
    <div className="auth-shell">
      <div className="auth-card">
        <div className="auth-side">
          <div className="auth-side__logo">
            <Logo variant={isDark ? "light" : "dark"} />
          </div>
          <IllustrationPanel variant={illustration} />
        </div>
        <div className="auth-form-panel">{children}</div>
      </div>
    </div>
  );
}
