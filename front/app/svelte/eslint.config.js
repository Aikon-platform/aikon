import js from "@eslint/js";
import globals from "globals";
import json from "@eslint/json";
import css from "@eslint/css";
import svelte from "eslint-plugin-svelte";
import { defineConfig, globalIgnores } from "eslint/config";
import stylistic from "@stylistic/eslint-plugin";

const baseRules = {
    "no-unused-vars": "off",
    "no-undef": "warning",
    "quotes": "off",
    "@stylistic/indent": ["warning", 4],
};

/** https://eslint.org/docs/latest/use/configure/rules */
export default defineConfig([
    // js.configs.recommended,
    // ...svelte.configs.recommended,
    {
        files: ["**/*.{js,mjs,cjs}"],
        plugins: {
            "@stylistic": stylistic,
            "js": js,
        },
        extends: ["js/recommended"],
        languageOptions: {
            globals: { ...globals.browser, ...globals.node },
        },
        rules: baseRules
    },
    {
        files: ["**/*.svelte", "**/*.svelte.js"],
        plugins: {
            "@stylistic": stylistic,
            "svelte": svelte,
        },
        extends: ["svelte/recommended"],
        languageOptions: {
            globals: { ...globals.browser, ...globals.node },
        },
        rules: {
            ...baseRules,
            "svelte/require-each-key": "off",
            "svelte/no-at-html-tags": "warn"
        },
    },
    {
        files: ["**/*.json"],
        plugins: { json },
        language: "json/json",
        extends: ["json/recommended"],
    },
    {
        files: ["**/*.css"],
        plugins: { css },
        language: "css/css",
        extends: ["css/recommended"],
    },
    globalIgnores(["package-lock.json"]),
]);
