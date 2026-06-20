import { Monitor, Moon, Sun } from "lucide-react";

import { useTheme } from "../context/ThemeContext";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const next = theme === "light" ? "dark" : theme === "dark" ? "system" : "light";
  const Icon = theme === "light" ? Sun : theme === "dark" ? Moon : Monitor;
  return (
    <button
      onClick={() => setTheme(next)}
      className="rounded-md p-2 hover:bg-surface text-muted hover:text-text transition"
      aria-label={`Сменить тему (сейчас: ${theme})`}
    >
      <Icon className="w-5 h-5" />
    </button>
  );
}
