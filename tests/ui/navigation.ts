import { vi } from "vitest";
export const navigation = {
  pathname: "/experiment-studio",
  router: { replace: vi.fn(), push: vi.fn(), refresh: vi.fn() },
};
