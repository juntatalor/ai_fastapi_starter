import { type ReactNode } from "react";
import { Navigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

interface Props {
  children: ReactNode;
  role?: "user" | "admin";
}

export function ProtectedRoute({ children, role }: Props) {
  const { user, loading } = useAuth();
  if (loading) return <div className="p-8 text-text">Загрузка…</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (role === "admin" && user.role !== "admin") {
    return <div className="p-8 text-text">403 — нет доступа.</div>;
  }
  return <>{children}</>;
}
