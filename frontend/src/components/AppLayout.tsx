import { LogOut } from "lucide-react";
import { Link, Outlet } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import { ThemeToggle } from "./ThemeToggle";

export function AppLayout() {
  const { user, logout, config } = useAuth();
  return (
    <div className="min-h-full flex flex-col bg-bg text-text">
      <header className="border-b border-border bg-surface">
        <div className="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <span className="font-semibold">{config?.app_name ?? "App"}</span>
            <nav className="flex gap-4 text-sm">
              <Link to="/" className="hover:text-primary">
                Главная
              </Link>
              <Link to="/profile" className="hover:text-primary">
                Профиль
              </Link>
              {user?.role === "admin" && (
                <Link to="/admin/users" className="hover:text-primary">
                  Пользователи
                </Link>
              )}
            </nav>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm text-muted">{user?.full_name ?? user?.email}</span>
            <ThemeToggle />
            <button
              onClick={logout}
              className="rounded-md p-2 hover:bg-bg text-muted hover:text-text"
              aria-label="Выйти"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>
      </header>
      <main className="flex-1">
        <div className="max-w-5xl mx-auto px-4 py-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
