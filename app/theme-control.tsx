"use client";

import { useEffect, useRef, useSyncExternalStore } from "react";

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
  const changing = useRef(false);
  const toggleTheme = async (event: React.MouseEvent<HTMLButtonElement>) => {
    if (changing.current) return;
    const next = theme === "dark" ? "light" : "dark";
    const commit = () => {
      applyTheme(next);
      try {
        localStorage.setItem(preferenceKey, next);
      } catch {
        // The current page remains usable when storage is blocked.
      }
    };
    if (
      !document.startViewTransition ||
      window.matchMedia("(prefers-reduced-motion: reduce)").matches ||
      !document.documentElement.animate
    ) {
      commit();
      return;
    }
    changing.current = true;
    const bounds = event.currentTarget.getBoundingClientRect();
    const x = bounds.left + bounds.width / 2;
    const y = bounds.top + bounds.height / 2;
    const radius = Math.hypot(
      Math.max(x, window.innerWidth - x),
      Math.max(y, window.innerHeight - y),
    );
    document.documentElement.dataset.themeReveal = "true";
    try {
      const transition = document.startViewTransition(commit);
      await transition.ready;
      await document.documentElement.animate(
        {
          clipPath: [
            `circle(0px at ${x}px ${y}px)`,
            `circle(${radius}px at ${x}px ${y}px)`,
          ],
        },
        {
          duration: 420,
          easing: "cubic-bezier(0.22, 1, 0.36, 1)",
          pseudoElement: "::view-transition-new(root)",
        },
      ).finished;
      await transition.finished;
    } catch {
      commit();
    } finally {
      delete document.documentElement.dataset.themeReveal;
      changing.current = false;
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
      <span className="theme-switch-track" aria-hidden="true">
        <span className="theme-switch-thumb" />
        <svg viewBox="0 0 24 24" fill="none" focusable="false">
          <path d="M20 15.4A8.5 8.5 0 0 1 8.6 4 8.5 8.5 0 1 0 20 15.4Z" />
        </svg>
        <svg viewBox="0 0 24 24" fill="none" focusable="false">
          <circle cx="12" cy="12" r="4" />
          <path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.4 1.4m11.2 11.2L19 19M5 19l1.4-1.4M17.6 6.4 19 5" />
        </svg>
      </span>
    </button>
  );
}
