import { api } from "./client";

export interface UserOut {
  id: number;
  email: string;
  full_name: string | null;
  role: "user" | "admin";
  is_active: boolean;
  has_password: boolean;
  has_yandex: boolean;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  const { data } = await api.post<TokenResponse>("/auth/login", { email, password });
  return data;
}

export async function me(): Promise<UserOut> {
  const { data } = await api.get<UserOut>("/auth/me");
  return data;
}

export async function changePassword(body: {
  current_password: string | null;
  new_password: string;
}): Promise<void> {
  await api.post("/auth/password", body);
}

export const yandexStartUrl = "/api/v1/auth/yandex/start";
