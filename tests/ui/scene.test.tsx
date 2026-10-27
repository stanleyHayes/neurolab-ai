import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, expect, it, vi } from "vitest";
import MaizeScene from "../../app/maize-scene";

const renderer = vi.hoisted(() => ({
  fail: false,
  frameloop: vi.fn(),
  controls: {
    getAzimuthalAngle: vi.fn(() => 0),
    setAzimuthalAngle: vi.fn(),
    getPolarAngle: vi.fn(() => 1),
    setPolarAngle: vi.fn(),
    dollyIn: vi.fn(),
    dollyOut: vi.fn(),
    update: vi.fn(),
  },
}));
vi.mock("@react-three/fiber", () => ({
  Canvas: ({ children }: Readonly<{ children: React.ReactNode }>) => {
    if (renderer.fail) throw new Error("Fixture renderer failure");
    return <section data-testid="renderer-fixture">{children}</section>;
  },
  useThree: (
    selector: (state: {
      setFrameloop: typeof renderer.frameloop;
      gl: { domElement: HTMLCanvasElement };
    }) => unknown,
  ) =>
    selector({
      setFrameloop: renderer.frameloop,
      gl: { domElement: document.createElement("canvas") },
    }),
}));
vi.mock("@react-three/drei", async () => {
  const react = await import("react");
  return {
    OrbitControls: react.forwardRef(function FixtureControls(_props, ref) {
      react.useImperativeHandle(ref, () => renderer.controls);
      return null;
    }),
  };
});
beforeEach(() => {
  renderer.fail = false;
  vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockImplementation(
    () =>
      ({
        getExtension: () => ({ loseContext: vi.fn() }),
      }) as unknown as WebGLRenderingContext,
  );
});

it("dispatches all keyboard camera controls through the typed renderer boundary", async () => {
  // jsdom has no Three.js renderer: this is a contract test, not GPU or visual evidence.
  vi.spyOn(console, "error").mockImplementation(() => undefined);
  render(<MaizeScene reducedMotion={false} />);
  await screen.findByTestId("renderer-fixture");
  fireEvent.click(screen.getByRole("button", { name: "Rotate camera left" }));
  fireEvent.click(screen.getByRole("button", { name: "Rotate camera right" }));
  fireEvent.click(screen.getByRole("button", { name: "Tilt camera up" }));
  fireEvent.click(screen.getByRole("button", { name: "Tilt camera down" }));
  fireEvent.click(screen.getByRole("button", { name: "Zoom in" }));
  fireEvent.click(screen.getByRole("button", { name: "Zoom out" }));
  expect(renderer.controls.setAzimuthalAngle).toHaveBeenCalledWith(-0.18);
  expect(renderer.controls.setAzimuthalAngle).toHaveBeenCalledWith(0.18);
  expect(renderer.controls.dollyIn).toHaveBeenCalledWith(1.18);
  expect(renderer.controls.dollyOut).toHaveBeenCalledWith(1.18);
  expect(renderer.controls.update).toHaveBeenCalledTimes(6);
  fireEvent.click(screen.getByRole("button", { name: "Reset view" }));
  expect(screen.getByText("SCHEMATIC · NOT MEASURED MORPHOLOGY")).toBeTruthy();
});

it("retains a static illustration with reduced motion or no WebGL", async () => {
  vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockReturnValue(null);
  render(<MaizeScene reducedMotion={true} />);
  await waitFor(() =>
    expect(screen.getByText("STATIC ILLUSTRATION")).toBeTruthy(),
  );
  expect(screen.queryByTestId("renderer-fixture")).toBeNull();
  expect(screen.queryByRole("button", { name: "Zoom in" })).toBeNull();
});

it("uses the fallback when renderer creation throws", async () => {
  renderer.fail = true;
  vi.spyOn(console, "error").mockImplementation(() => undefined);
  render(<MaizeScene reducedMotion={false} />);
  await waitFor(() =>
    expect(screen.getByRole("button", { name: "Reset view" })).toBeTruthy(),
  );
  expect(screen.queryByTestId("renderer-fixture")).toBeNull();
  expect(screen.getByText("SCHEMATIC · NOT MEASURED MORPHOLOGY")).toBeTruthy();
});
