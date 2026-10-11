#!/usr/bin/env node
const fs = require("fs");
const path = require("path");

const env = process.argv[2] || "local";
const validEnvs = ["local", "prod"];

if (!validEnvs.includes(env)) {
  console.error(`Error: Environment must be one of: ${validEnvs.join(", ")}`);
  process.exit(1);
}

console.log(`Setting up environment: ${env}`);

const sourcePath = path.join(process.cwd(), `.env.${env}`);
const destPath = path.join(process.cwd(), ".env");

if (!fs.existsSync(sourcePath)) {
  console.error(`Error: Environment file ${sourcePath} does not exist`);
  process.exit(1);
}

fs.copyFileSync(sourcePath, destPath);
console.log(`Copied ${sourcePath} to ${destPath}`);

const localPath = path.join(process.cwd(), ".env.local");
if (fs.existsSync(localPath)) {
  console.log("Local overrides detected. These will take precedence.");
}

console.log("Environment setup complete!");
