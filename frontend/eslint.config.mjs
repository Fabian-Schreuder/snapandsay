import { FlatCompat } from "@eslint/eslintrc";

const compat = new FlatCompat({
  baseDirectory: import.meta.dirname,
});

const eslintConfig = [
  {
    ignores: [
      "node_modules/**",
      ".next/**",
      "out/**",
      "build/**",
      "next-env.d.ts",
    ],
  },
  ...compat.config({
    extends: ["next/core-web-vitals", "next/typescript", "prettier"],
    rules: { "@typescript-eslint/no-empty-object-type": "off" },
    overrides: [
      {
        // Relax rules for test files
        files: [
          "**/__tests__/**/*",
          "**/*.test.ts",
          "**/*.test.tsx",
          "jest.setup.ts",
        ],
        rules: {
          "@typescript-eslint/no-explicit-any": "off",
          "@typescript-eslint/no-require-imports": "off",
          "@typescript-eslint/no-unused-vars": "warn",
          "@typescript-eslint/ban-ts-comment": "off",
          "react/display-name": "off",
          "@next/next/no-img-element": "off",
        },
      },
    ],
  }),
];

export default eslintConfig;
