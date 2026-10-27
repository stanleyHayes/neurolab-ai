"use client";

import { useEffect, useSyncExternalStore } from "react";

type Theme = "dark" | "light";
const preferenceKey = "neurolab-theme";
const changeEvent = "neurolab-theme-change";

function applyTheme(theme: Theme) {
  document.documentElement.dataset.theme = theme;
  window.dispatchEvent(new Event(changeEvent));
}

function subscribe(listener: () => void) {
  window.addEventListener(changeEvent, listener);
  return () => window.removeEventListener(changeEvent, listener);
}

function currentTheme(): Theme {
  return document.documentElement.dataset.theme === "light" ? "light" : "dark";
}

export function ThemePreference() {
  useEffect(() => {
    try {
      applyTheme(
        localStorage.getItem(preferenceKey) === "light" ? "light" : "dark",
      );
    } catch {
      // A blocked preference store must not prevent access to research.
      applyTheme("dark");
    }
    const syncPreference = (event: StorageEvent) => {
      if (event.key === preferenceKey || event.key === null) {
        applyTheme(event.newValue === "light" ? "light" : "dark");
      }
    };
    window.addEventListener("storage", syncPreference);
    return () => window.removeEventListener("storage", syncPreference);
  }, []);
  return null;
}

export function ThemeControl() {
  const theme = useSyncExternalStore(subscribe, currentTheme, () => "dark");
  const toggleTheme = () => {
    const next = theme === "dark" ? "light" : "dark";
    applyTheme(next);
    try {
      localStorage.setItem(preferenceKey, next);
    } catch {
      // The choice still works for this page when storage is unavailable.
    }
  };
  return (
    <button
      className="theme-control"
      type="button"
      aria-label="Light mode"
      aria-pressed={theme === "light"}
      title={theme === "light" ? "Switch to dark mode" : "Switch to light mode"}
      onClick={toggleTheme}
    >
      <svg viewBox="0 0 24 24" fill="none" aria-hidden="true" focusable="false">
        <circle cx="12" cy="12" r="4" />
        <path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.4 1.4m11.2 11.2L19 19M5 19l1.4-1.4M17.6 6.4 19 5" />
      </svg>
      <span>{theme === "light" ? "Light" : "Dark"}</span>
    </button>
  );
}
