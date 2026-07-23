import { useState, type FormEvent } from "react";

import { changePassword } from "../api/auth";
import { useAuth } from "../context/AuthContext";

export function ProfilePage() {
  const { user, refreshMe } = useAuth();
  const [currentPassword, setCurrent] = useState("");
  const [newPassword, setNew] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setMsg(null);
    setError(null);
    try {
      await changePassword({
        current_password: user?.has_password ? currentPassword : null,
        new_password: newPassword,
      });
      setMsg("Пароль обновлён.");
      setCurrent("");
      setNew("");
      await refreshMe();
    } catch (e: unknown) {
      const detail =
        (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? null;
      setError(detail ?? "Не удалось сменить пароль");
    }
  }

  return (
    <div className="max-w-md">
      <h1 className="text-2xl font-semibold">Профиль</h1>
      <div className="mt-4 space-y-1 text-sm">
        <div>
          <span className="text-muted">Email:</span> {user?.email}
        </div>
        <div>
          <span className="text-muted">Роль:</span> {user?.role}
        </div>
        <div>
          <span className="text-muted">Yandex:</span> {user?.has_yandex ? "привязан" : "—"}
        </div>
      </div>
      <h2 className="text-lg font-medium mt-8">
        {user?.has_password ? "Сменить пароль" : "Установить пароль"}
      </h2>
      <form onSubmit={onSubmit} className="mt-4 space-y-3">
        {user?.has_password && (
          <input
            type="password"
            placeholder="Текущий пароль"
            required
            value={currentPassword}
            onChange={(e) => setCurrent(e.target.value)}
            className="w-full rounded-md bg-surface border border-border px-3 py-2 text-text"
          />
        )}
        <input
          type="password"
          placeholder="Новый пароль (8+ символов)"
          required
          minLength={8}
          value={newPassword}
          onChange={(e) => setNew(e.target.value)}
          className="w-full rounded-md bg-surface border border-border px-3 py-2 text-text"
        />
        {error && <p className="text-sm text-red-500 dark:text-red-400">{error}</p>}
        {msg && <p className="text-sm text-emerald-600 dark:text-emerald-400">{msg}</p>}
        <button
          type="submit"
          className="rounded-md bg-primary text-white px-4 py-2 font-medium hover:opacity-90"
        >
          Обновить
        </button>
      </form>
    </div>
  );
}
