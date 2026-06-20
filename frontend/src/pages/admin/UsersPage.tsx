import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { KeyRound, Pencil, Trash2, UserPlus } from "lucide-react";
import { useState } from "react";

import { createUser, deleteUser, listUsers, resetPassword, updateUser } from "../../api/admin";
import type { UserOut } from "../../api/auth";

type Role = "user" | "admin";

interface CreateForm {
  email: string;
  full_name: string;
  role: Role;
  password: string;
}

interface EditForm {
  id: number;
  full_name: string;
  role: Role;
  is_active: boolean;
}

export function UsersPage() {
  const qc = useQueryClient();
  const { data: users = [], isLoading } = useQuery({
    queryKey: ["admin-users"],
    queryFn: listUsers,
  });

  const [createOpen, setCreateOpen] = useState(false);
  const [editing, setEditing] = useState<EditForm | null>(null);
  const [resettingFor, setResettingFor] = useState<UserOut | null>(null);
  const [newPassword, setNewPassword] = useState("");

  const invalidate = () => qc.invalidateQueries({ queryKey: ["admin-users"] });

  const createMut = useMutation({
    mutationFn: (form: CreateForm) =>
      createUser({
        email: form.email,
        full_name: form.full_name || null,
        role: form.role,
        password: form.password || null,
      }),
    onSuccess: () => {
      invalidate();
      setCreateOpen(false);
    },
  });

  const updateMut = useMutation({
    mutationFn: (form: EditForm) =>
      updateUser(form.id, {
        full_name: form.full_name || null,
        role: form.role,
        is_active: form.is_active,
      }),
    onSuccess: () => {
      invalidate();
      setEditing(null);
    },
  });

  const resetMut = useMutation({
    mutationFn: (args: { id: number; new_password: string }) =>
      resetPassword(args.id, args.new_password),
    onSuccess: () => {
      setResettingFor(null);
      setNewPassword("");
    },
  });

  const deleteMut = useMutation({
    mutationFn: (id: number) => deleteUser(id),
    onSuccess: invalidate,
  });

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold">Пользователи</h1>
        <button
          onClick={() => setCreateOpen(true)}
          className="inline-flex items-center gap-2 rounded-md bg-primary text-white px-3 py-2 text-sm font-medium hover:opacity-90"
        >
          <UserPlus className="w-4 h-4" />
          Пользователь
        </button>
      </div>

      {isLoading ? (
        <p className="text-muted">Загрузка…</p>
      ) : (
        <div className="overflow-x-auto bg-surface border border-border rounded-lg">
          <table className="w-full text-sm">
            <thead className="border-b border-border text-muted">
              <tr>
                <th className="text-left px-4 py-2 font-medium">Email</th>
                <th className="text-left px-4 py-2 font-medium">Имя</th>
                <th className="text-left px-4 py-2 font-medium">Роль</th>
                <th className="text-left px-4 py-2 font-medium">Активен</th>
                <th className="text-right px-4 py-2 font-medium">Действия</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-b border-border last:border-0">
                  <td className="px-4 py-2">{u.email}</td>
                  <td className="px-4 py-2">{u.full_name ?? "—"}</td>
                  <td className="px-4 py-2">{u.role}</td>
                  <td className="px-4 py-2">{u.is_active ? "✓" : "—"}</td>
                  <td className="px-4 py-2 text-right whitespace-nowrap">
                    <button
                      onClick={() =>
                        setEditing({
                          id: u.id,
                          full_name: u.full_name ?? "",
                          role: u.role,
                          is_active: u.is_active,
                        })
                      }
                      className="text-muted hover:text-primary p-1.5"
                      aria-label="Изменить"
                      title="Изменить"
                    >
                      <Pencil className="w-4 h-4 inline" />
                    </button>
                    <button
                      onClick={() => setResettingFor(u)}
                      className="text-muted hover:text-primary p-1.5"
                      aria-label="Сбросить пароль"
                      title="Сбросить пароль"
                    >
                      <KeyRound className="w-4 h-4 inline" />
                    </button>
                    <button
                      onClick={() => {
                        if (confirm(`Деактивировать ${u.email}?`)) deleteMut.mutate(u.id);
                      }}
                      className="text-muted hover:text-red-500 p-1.5"
                      aria-label="Удалить"
                      title="Деактивировать"
                    >
                      <Trash2 className="w-4 h-4 inline" />
                    </button>
                  </td>
                </tr>
              ))}
              {users.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-6 text-center text-muted">
                    Пусто. Добавь первого пользователя кнопкой выше.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {createOpen && (
        <CreateUserModal
          onClose={() => setCreateOpen(false)}
          onSubmit={(form) => createMut.mutate(form)}
          error={(createMut.error as Error | null)?.message ?? null}
        />
      )}

      {editing && (
        <EditUserModal
          form={editing}
          onClose={() => setEditing(null)}
          onChange={setEditing}
          onSubmit={() => updateMut.mutate(editing)}
        />
      )}

      {resettingFor && (
        <Modal
          title={`Сброс пароля: ${resettingFor.email}`}
          onClose={() => {
            setResettingFor(null);
            setNewPassword("");
          }}
        >
          <input
            type="password"
            placeholder="Новый пароль (8+ символов)"
            required
            minLength={8}
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            className="w-full rounded-md bg-bg border border-border px-3 py-2 text-text"
          />
          <button
            onClick={() =>
              resetMut.mutate({ id: resettingFor.id, new_password: newPassword })
            }
            className="rounded-md bg-primary text-white px-4 py-2 font-medium hover:opacity-90"
          >
            Сбросить
          </button>
        </Modal>
      )}
    </div>
  );
}

function CreateUserModal({
  onClose,
  onSubmit,
  error,
}: {
  onClose: () => void;
  onSubmit: (form: CreateForm) => void;
  error: string | null;
}) {
  const [form, setForm] = useState<CreateForm>({
    email: "",
    full_name: "",
    role: "user",
    password: "",
  });
  return (
    <Modal title="Новый пользователь" onClose={onClose}>
      <input
        type="email"
        placeholder="Email"
        required
        value={form.email}
        onChange={(e) => setForm({ ...form, email: e.target.value })}
        className="w-full rounded-md bg-bg border border-border px-3 py-2 text-text"
      />
      <input
        type="text"
        placeholder="Имя (опционально)"
        value={form.full_name}
        onChange={(e) => setForm({ ...form, full_name: e.target.value })}
        className="w-full rounded-md bg-bg border border-border px-3 py-2 text-text"
      />
      <select
        value={form.role}
        onChange={(e) => setForm({ ...form, role: e.target.value as Role })}
        className="w-full rounded-md bg-bg border border-border px-3 py-2 text-text"
      >
        <option value="user">user</option>
        <option value="admin">admin</option>
      </select>
      <input
        type="password"
        placeholder="Пароль (опционально — иначе только через Yandex)"
        minLength={8}
        value={form.password}
        onChange={(e) => setForm({ ...form, password: e.target.value })}
        className="w-full rounded-md bg-bg border border-border px-3 py-2 text-text"
      />
      {error && <p className="text-sm text-red-500 dark:text-red-400">{error}</p>}
      <button
        onClick={() => onSubmit(form)}
        className="rounded-md bg-primary text-white px-4 py-2 font-medium hover:opacity-90"
      >
        Создать
      </button>
    </Modal>
  );
}

function EditUserModal({
  form,
  onClose,
  onChange,
  onSubmit,
}: {
  form: EditForm;
  onClose: () => void;
  onChange: (f: EditForm) => void;
  onSubmit: () => void;
}) {
  return (
    <Modal title="Изменить пользователя" onClose={onClose}>
      <input
        type="text"
        placeholder="Имя"
        value={form.full_name}
        onChange={(e) => onChange({ ...form, full_name: e.target.value })}
        className="w-full rounded-md bg-bg border border-border px-3 py-2 text-text"
      />
      <select
        value={form.role}
        onChange={(e) => onChange({ ...form, role: e.target.value as Role })}
        className="w-full rounded-md bg-bg border border-border px-3 py-2 text-text"
      >
        <option value="user">user</option>
        <option value="admin">admin</option>
      </select>
      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={form.is_active}
          onChange={(e) => onChange({ ...form, is_active: e.target.checked })}
        />
        Активен
      </label>
      <button
        onClick={onSubmit}
        className="rounded-md bg-primary text-white px-4 py-2 font-medium hover:opacity-90"
      >
        Сохранить
      </button>
    </Modal>
  );
}

function Modal({
  title,
  onClose,
  children,
}: {
  title: string;
  onClose: () => void;
  children: React.ReactNode;
}) {
  return (
    <div
      className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-md bg-surface border border-border rounded-lg p-6 shadow-lg space-y-4"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">{title}</h2>
          <button onClick={onClose} className="text-muted hover:text-text text-xl leading-none">
            ×
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
