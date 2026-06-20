import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";

import { yandexStartUrl } from "../api/auth";
import { ThemeToggle } from "../components/ThemeToggle";
import { useAuth } from "../context/AuthContext";

export function LoginPage() {
  const { login, config, user } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  // Уже залогинен — отправляем на главную.
  if (user) {
    navigate("/", { replace: true });
    return null;
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await login(email, password);
      navigate("/");
    } catch {
      setError("Неверный email или пароль");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-full flex items-center justify-center bg-bg p-4">
      <div className="absolute top-3 right-3">
        <ThemeToggle />
      </div>
      <form
        onSubmit={onSubmit}
        className="w-full max-w-sm bg-surface border border-border rounded-lg p-6 shadow-sm space-y-4"
      >
        <h1 className="text-xl font-semibold text-text">{config?.app_name ?? "Login"}</h1>
        <input
          type="email"
          placeholder="Email"
          required
          autoFocus
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full rounded-md bg-bg border border-border px-3 py-2 text-text"
        />
        <input
          type="password"
          placeholder="Пароль"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full rounded-md bg-bg border border-border px-3 py-2 text-text"
        />
        {error && <p className="text-sm text-red-500 dark:text-red-400">{error}</p>}
        <button
          type="submit"
          disabled={busy}
          className="w-full rounded-md bg-primary text-white py-2 font-medium hover:opacity-90 disabled:opacity-50"
        >
          {busy ? "Вход…" : "Войти"}
        </button>
        {config?.yandex_enabled && (
          <a
            href={yandexStartUrl}
            className="block text-center text-sm text-primary hover:underline"
          >
            Войти через Яндекс
          </a>
        )}
      </form>
    </div>
  );
}
