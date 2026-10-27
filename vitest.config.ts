import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "jsdom",
    include: ["tests/ui/**/*.test.tsx", "tests/ui/**/*.test.ts"],
    setupFiles: ["tests/ui/setup.tsx"],
    coverage: {
      provider: "v8",
      reporter: ["text", "lcov"],
      reportsDirectory: "coverage/ui",
      include: [
        "app/**/*.tsx",
        "app/auth-client.ts",
        "app/workspace/workspace-config.ts",
      ],
    },
  },
});
