import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";
import eslint from "@eslint/js";
import { defineConfig, globalIgnores } from "eslint/config";
import globals from "globals";
import tseslint from "typescript-eslint";

const tsconfigRootDir = path.dirname(fileURLToPath(import.meta.url));

const require = createRequire(import.meta.url);
const { flatConfig } = require("@next/eslint-plugin-next");

const nextCoreWebVitalsBlocks = Array.isArray(flatConfig.coreWebVitals)
    ? flatConfig.coreWebVitals
    : [flatConfig.coreWebVitals];

const actionGuardNames =
    "createPublicAction|selfUserAction|platformAdminAction";
const routeAuthNames = "requireUser|requirePlatformAdmin";

const actionFileRules = {
    "no-restricted-syntax": [
        "error",
        {
            selector:
                "ExportNamedDeclaration[declaration.type='FunctionDeclaration'][declaration.async=true]",
            message:
                "Exported async functions are not allowed in action files. Use `export const` values created via createPublicAction, selfUserAction, or platformAdminAction.",
        },
        {
            selector:
                "ExportNamedDeclaration > VariableDeclaration[kind!='const']",
            message:
                "Use `export const` in action files; do not export `let` or `var`.",
        },
        {
            selector: `ExportNamedDeclaration > VariableDeclaration > VariableDeclarator[id.name=/Action$/]:not(:has(CallExpression[callee.name=/^(${actionGuardNames})$/]))`,
            message: `Exported *Action values must be created via createPublicAction, selfUserAction, or platformAdminAction (from @fiery/auth/server).`,
        },
    ],
};

const apiRouteRules = {
    "no-restricted-syntax": [
        "error",
        {
            selector: `ExportNamedDeclaration > FunctionDeclaration[id.name=/^(GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)$/]:not(:has(CallExpression[callee.name=/^(${routeAuthNames})$/]))`,
            message: `Route handlers must call requireUser or requirePlatformAdmin (from @fiery/auth/server).`,
        },
    ],
};

export default defineConfig([
    globalIgnores([
        "**/node_modules/**",
        "**/dist/**",
        "**/.next/**",
        "**/next-env.d.ts",
        "**/out/**",
        "**/build/**",
        "**/coverage/**",
        "**/prisma/src/generated/**",
        "**/public/maplibre/**",
        "**/public/**/*.mjs",
        "**/*.py",
        "**/__pycache__/**",
        "**/.venv/**",
        "**/*.egg-info/**",
    ]),
    eslint.configs.recommended,
    ...tseslint.configs.recommended,
    ...nextCoreWebVitalsBlocks.map((block) => ({
        ...block,
        files: block.files ?? ["apps/*/**/*.{js,jsx,mjs,cjs,ts,tsx}"],
    })),
    {
        files: ["**/*.{ts,tsx}"],
        languageOptions: {
            parserOptions: {
                tsconfigRootDir,
            },
        },
    },
    {
        files: [
            "apps/*/app/**/actions.ts",
            "apps/*/app/**/actions/*.ts",
            "apps/*/app/**/(actions)/**/*.ts",
            "apps/*/app/**/actions/**/*.ts",
            "apps/*/lib/**/actions.ts",
            "apps/*/lib/**/(actions)/**/*.ts",
            "apps/*/lib/**/actions/*.ts",
            "apps/*/lib/**/actions/**/*.ts",
        ],
        rules: actionFileRules,
    },
    {
        files: ["apps/*/app/api/**/route.ts"],
        rules: apiRouteRules,
    },
    {
        files: ["scripts/*.js"],
        languageOptions: {
            globals: {
                ...globals.node,
                ...globals.commonjs,
            },
        },
        rules: {
            "@typescript-eslint/no-require-imports": "off",
        },
    },
    {
        rules: {
            "@next/next/no-html-link-for-pages": "off",
        },
    },
]);
