import { useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";

export function YandexCallbackPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const { refreshMe } = useAuth();

  useEffect(() => {
    const code = params.get("code");
    if (!code) {
      navigate("/login", { replace: true });
      return;
    }
    api
      .get<{ access_token: string }>(`/auth/yandex/callback?code=${encodeURIComponent(code)}`)
      .then(async (r) => {
        localStorage.setItem("token", r.data.access_token);
        await refreshMe();
        navigate("/", { replace: true });
      })
      .catch(() => navigate("/login?yandex_failed=1", { replace: true }));
  }, [params, navigate, refreshMe]);

  return <div className="p-8 text-text">Авторизация через Яндекс…</div>;
}
