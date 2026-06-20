import { useAuth } from "../context/AuthContext";

export function HelloPage() {
  const { user } = useAuth();
  return (
    <div>
      <h1 className="text-2xl font-semibold">Hello, {user?.full_name ?? user?.email}!</h1>
      <p className="text-muted mt-2">
        Это стартовая страница для пользователя. Заполни здесь домен-специфичный UI.
      </p>
    </div>
  );
}
