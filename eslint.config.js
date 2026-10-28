import globals from "globals";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTypeScript from "eslint-config-next/typescript";

const eslintConfig = [
  {
    ignores: [
      ".venv/**",
      "venv/**",
      "coverage/**",
      ".test-build/**",
      ".scannerwork/**",
      "data/**",
      "eval/**",
      "node_modules/**",
      ".next/**",
      "out/**",
      "output/demo-video/**",
      "build/**",
      "next-env.d.ts",
      "**/__pycache__/**",
    ],
  },
  ...nextVitals,
  ...nextTypeScript,
  {
    files: ["scripts/**/*.js"],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "script",
      globals: { ...globals.browser, ...globals.node },
    },
    rules: {
      "array-callback-return": "error",
      "constructor-super": "error",
      curly: ["error", "all"],
      eqeqeq: ["error", "always"],
      "no-async-promise-executor": "error",
      "no-console": "warn",
      "no-debugger": "error",
      "no-duplicate-imports": "error",
      "no-implicit-coercion": "error",
      "no-promise-executor-return": "error",
      "no-self-compare": "error",
      "no-template-curly-in-string": "error",
      "no-unmodified-loop-condition": "error",
      "no-unreachable-loop": "error",
      "no-unsafe-optional-chaining": "error",
      "no-unused-private-class-members": "error",
      "no-unused-vars": [
        "error",
        { argsIgnorePattern: "^_", caughtErrorsIgnorePattern: "^_" },
      ],
      "no-use-before-define": ["error", { functions: false }],
      "object-shorthand": ["error", "always"],
      "prefer-const": "error",
      "prefer-template": "error",
      "require-atomic-updates": "error",
      "require-yield": "error",
      "use-isnan": "error",
      yoda: "error",
    },
  },
  {
    files: ["app/**/*.{ts,tsx}"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      globals: { ...globals.browser, ...globals.node },
    },
  },
];

export default eslintConfig;
