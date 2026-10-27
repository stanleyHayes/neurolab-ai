import React from "react";
import { readFileSync } from "node:fs";
import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ThemeControl, ThemePreference } from "../../app/theme-control";

beforeEach(() => {
  localStorage.clear();
  delete document.documentElement.dataset.theme;
});
afterEach(() => {
  vi.restoreAllMocks();
  localStorage.clear();
  delete document.documentElement.dataset.theme;
});

describe("research appearance preference", () => {
  it("restores a light preference, exposes state and persists a toggle", () => {
    localStorage.setItem("neurolab-theme", "light");
    render(
      <>
        <ThemePreference />
        <ThemeControl />
      </>,
    );
    const button = screen.getByRole("button", { name: "Light mode" });
    expect(button.getAttribute("aria-pressed")).toBe("true");
    expect(document.documentElement.dataset.theme).toBe("light");
    fireEvent.click(button);
    expect(button.getAttribute("aria-pressed")).toBe("false");
    expect(localStorage.getItem("neurolab-theme")).toBe("dark");
  });

  it("reveals the new theme from the control when motion is allowed", async () => {
    vi.spyOn(window, "matchMedia").mockReturnValue({
      matches: false,
    } as MediaQueryList);
    const animate = vi.fn(() => ({ finished: Promise.resolve() }));
    const transition = vi.fn((update: () => void) => {
      update();
      return { ready: Promise.resolve(), finished: Promise.resolve() };
    });
    Object.defineProperty(document, "startViewTransition", {
      configurable: true,
      value: transition,
    });
    Object.defineProperty(document.documentElement, "animate", {
      configurable: true,
      value: animate,
    });
    try {
      render(<ThemeControl />);
      fireEvent.click(screen.getByRole("button", { name: "Light mode" }));
      await waitFor(() =>
        expect(animate).toHaveBeenCalledWith(
          expect.objectContaining({
            clipPath: expect.arrayContaining(["circle(0px at 0px 0px)"]),
          }),
          expect.objectContaining({
            pseudoElement: "::view-transition-new(root)",
            duration: 420,
          }),
        ),
      );
      expect(document.documentElement.dataset.theme).toBe("light");
      await waitFor(() =>
        expect(document.documentElement.dataset.themeReveal).toBeUndefined(),
      );
    } finally {
      Reflect.deleteProperty(document, "startViewTransition");
      Reflect.deleteProperty(document.documentElement, "animate");
    }
  });

  it("synchronizes other-tab changes and ignores unrelated storage", () => {
    render(
      <>
        <ThemePreference />
        <ThemeControl />
      </>,
    );
    act(() =>
      window.dispatchEvent(
        new StorageEvent("storage", {
          key: "neurolab-theme",
          newValue: "light",
        }),
      ),
    );
    expect(document.documentElement.dataset.theme).toBe("light");
    act(() =>
      window.dispatchEvent(
        new StorageEvent("storage", {
          key: "unrelated",
          newValue: "dark",
        }),
      ),
    );
    expect(document.documentElement.dataset.theme).toBe("light");
    act(() => window.dispatchEvent(new StorageEvent("storage", { key: null })));
    expect(document.documentElement.dataset.theme).toBe("dark");
  });

  it("keeps the switch usable when preference storage is denied", () => {
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new Error("denied");
    });
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("denied");
    });
    render(
      <>
        <ThemePreference />
        <ThemeControl />
      </>,
    );
    const button = screen.getByRole("button", { name: "Light mode" });
    fireEvent.click(button);
    expect(button.getAttribute("aria-pressed")).toBe("true");
    expect(document.documentElement.dataset.theme).toBe("light");
  });
});

it("gives light-theme text tokens AA contrast against all daylight surfaces", () => {
  const css = readFileSync("app/globals.css", "utf8");
  const block = css.split(':root[data-theme="light"] {')[1].split("}")[0];
  const palette = Object.fromEntries(
    [...block.matchAll(/--([\w-]+): (#[\da-f]{6});/g)].map((match) => [
      match[1],
      match[2],
    ]),
  );
  const luminance = (hex: string) => {
    const rgb = [1, 3, 5]
      .map((offset) => Number.parseInt(hex.slice(offset, offset + 2), 16) / 255)
      .map((channel) =>
        channel <= 0.04045
          ? channel / 12.92
          : ((channel + 0.055) / 1.055) ** 2.4,
      );
    return rgb[0] * 0.2126 + rgb[1] * 0.7152 + rgb[2] * 0.0722;
  };
  const contrast = (a: string, b: string) => {
    const values = [luminance(a), luminance(b)].sort((x, y) => y - x);
    return (values[0] + 0.05) / (values[1] + 0.05);
  };
  for (const surface of ["bg", "panel", "panel-raised", "day-surface-accent"]) {
    for (const ink of ["text", "muted", "green", "gold", "cyan", "red"]) {
      expect(
        contrast(palette[ink], palette[surface]),
        `${ink} on ${surface}`,
      ).toBeGreaterThanOrEqual(4.5);
    }
    expect(
      contrast(palette.line, palette[surface]),
      `control border on ${surface}`,
    ).toBeGreaterThanOrEqual(3);
  }
});
