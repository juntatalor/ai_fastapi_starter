import { api } from "./client";

export interface PublicConfig {
  app_name: string;
  yandex_enabled: boolean;
}

export async function fetchConfig(): Promise<PublicConfig> {
  const { data } = await api.get<PublicConfig>("/config");
  return data;
}
