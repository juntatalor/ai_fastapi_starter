import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

import { login as apiLogin, me as apiMe, type UserOut } from "../api/auth";
import { fetchConfig, type PublicConfig } from "../api/config";

interface AuthContextValue {
  user: UserOut | null;
  config: PublicConfig | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshMe: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserOut | null>(null);
  const [config, setConfig] = useState<PublicConfig | null>(null);
  const [loading, setLoading] = useState(true);

  async function refreshMe() {
    try {
      const data = await apiMe();
      setUser(data);
    } catch {
      setUser(null);
    }
  }

  useEffect(() => {
    (async () => {
      try {
        const cfg = await fetchConfig();
        setConfig(cfg);
      } catch {
        setConfig(null);
      }
      if (localStorage.getItem("token")) await refreshMe();
      setLoading(false);
    })();
  }, []);

  async function login(email: string, password: string) {
    const { access_token } = await apiLogin(email, password);
    localStorage.setItem("token", access_token);
    await refreshMe();
  }

  function logout() {
    localStorage.removeItem("token");
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, config, loading, login, logout, refreshMe }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be inside AuthProvider");
  return ctx;
}
