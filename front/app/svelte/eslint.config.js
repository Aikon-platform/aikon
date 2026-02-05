import js from "@eslint/js";
import globals from "globals";
import json from "@eslint/json";
import css from "@eslint/css";
import { defineConfig, globalIgnores } from "eslint/config";
import stylistic from "@stylistic/eslint-plugin"

/** https://eslint.org/docs/latest/use/configure/rules */
export default defineConfig([
  {
    files: ["**/*.{js,mjs,cjs}"],
    plugins: {
      "js": js,
      "@stylistic": stylistic
    },
    extends: ["js/recommended"],
    languageOptions: { globals: {...globals.browser, ...globals.node} },
    rules: {
      "no-unused-vars": "off",
      "no-undef": "warn",
      "quotes": ["error", "double"],
      "@stylistic/indent": ["error", 2],
    },
  },
  { files: ["**/*.json"], plugins: { json }, language: "json/json", extends: ["json/recommended"] },
  { files: ["**/*.css"], plugins: { css }, language: "css/css", extends: ["css/recommended"] },
  globalIgnores(["package-lock.json"]),
]);
