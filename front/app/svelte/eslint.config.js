// import js from "@eslint/js";
// import globals from "globals";
// import json from "@eslint/json";
// import css from "@eslint/css";
// import svelte from "eslint-plugin-svelte";
// import { defineConfig, globalIgnores } from "eslint/config";
// import stylistic from "@stylistic/eslint-plugin"

/** https://eslint.org/docs/latest/use/configure/rules */
// export default defineConfig([
//   // js.configs.recommended,
//   svelte.configs.recommended,
//   {
//     files: ["**/*.{js,mjs,cjs}"],
//     plugins: {
//       "js": js,
//       "@stylistic": stylistic
//     },
//     extends: ["js/recommended"],
//     languageOptions: { globals: {...globals.browser, ...globals.node} },
//     rules: {
//       "no-unused-vars": "off",
//       "no-undef": "warn",
//       "quotes": ["error", "double"],
//       "@stylistic/indent": ["error", 2],
//     },
//   },
//   {
//     files: ['**/*.svelte', '**/*.svelte.js'],
//     languageOptions: { globals: {...globals.browser, ...globals.node} },
//     rules: {
//       "no-unused-vars": "off",
//       "no-undef": "warn",
//       "quotes": ["error", "double"],
//       "@stylistic/indent": ["error", 2],
//     },
//   },
//   { files: ["**/*.json"], plugins: { json }, language: "json/json", extends: ["json/recommended"] },
//   { files: ["**/*.css"], plugins: { css }, language: "css/css", extends: ["css/recommended"] },
//   globalIgnores(["package-lock.json"]),
// ]);

import js from "@eslint/js";
import globals from "globals";
import json from "@eslint/json";
import css from "@eslint/css";
import svelte from "eslint-plugin-svelte";
import { defineConfig, globalIgnores } from "eslint/config";
import stylistic from "@stylistic/eslint-plugin";

const baseRules = {
  "no-unused-vars": "off",
  "no-undef": "warn",
  "quotes": ["error", "double"],
  "@stylistic/indent": ["error", 2],
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

// export default [
//   js.configs.recommended,
//   ...svelte.configs.recommended,
//   {
//     languageOptions: {
//       globals: {
//         ...globals.browser,
//         // ...globals.node // Add this if you are using SvelteKit in non-SPA mode
//       }
//     },
//   },
//   {
//     files: ['**/*.svelte', '**/*.svelte.js'],
//     languageOptions: {
//       parserOptions: {
//         // We recommend importing and specifying svelte.config.js.
//         // By doing so, some rules in eslint-plugin-svelte will automatically read the configuration and adjust their behavior accordingly.
//         // While certain Svelte settings may be statically loaded from svelte.config.js even if you don’t specify it,
//         // explicitly specifying it ensures better compatibility and functionality.
//         //
//         // If non-serializable properties are included, running ESLint with the --cache flag will fail.
//         // In that case, please remove the non-serializable properties. (e.g. `svelteConfig: { ...svelteConfig, kit: { ...svelteConfig.kit, typescript: undefined }}`)
//         // svelteConfig
//       }
//     }
//   },
//   // {
//   //
//   //   files: ['**/*.svelte', '**/*.svelte.js'],
//   //   languageOptions: { globals: {...globals.browser, ...globals.node} },
//   //   // rules: {
//   //   //   "no-unused-vars": "off",
//   //   //   "no-undef": "warn",
//   //   //   "quotes": ["error", "double"],
//   //   //   "@stylistic/indent": ["error", 2],
//   //   // },
//   // },
//   { files: ["**/*.json"], plugins: { json }, language: "json/json", },
//   { files: ["**/*.css"], plugins: { css }, language: "css/css", },
//   globalIgnores(["package-lock.json"]),
// ];
