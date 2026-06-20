import { api } from "./client";
import type { UserOut } from "./auth";

export async function listUsers(): Promise<UserOut[]> {
  const { data } = await api.get<UserOut[]>("/admin/users");
  return data;
}

export async function createUser(body: {
  email: string;
  full_name?: string | null;
  role: "user" | "admin";
  password?: string | null;
}): Promise<UserOut> {
  const { data } = await api.post<UserOut>("/admin/users", body);
  return data;
}

export async function updateUser(
  id: number,
  body: { full_name?: string | null; role?: "user" | "admin"; is_active?: boolean },
): Promise<UserOut> {
  const { data } = await api.patch<UserOut>(`/admin/users/${id}`, body);
  return data;
}

export async function resetPassword(id: number, new_password: string): Promise<void> {
  await api.post(`/admin/users/${id}/password`, { new_password });
}

export async function deleteUser(id: number): Promise<void> {
  await api.delete(`/admin/users/${id}`);
}
