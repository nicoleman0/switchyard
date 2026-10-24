#!/usr/bin/env node
// Runs the bundled updater in --install mode against the bundled release.
import { spawnSync } from "node:child_process";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const usage = "usage: npx create-switchyard   (run from the root of a git repo)";
const args = process.argv.slice(2);

if (args.length === 1 && (args[0] === "--help" || args[0] === "-h")) {
  console.log(usage);
  process.exit(0);
}
if (args.length > 0) {
  console.error(usage);
  process.exit(2);
}

const dist = join(dirname(fileURLToPath(import.meta.url)), "..", "dist");
const result = spawnSync(
  "python3",
  [join(dist, "update-switchyard.py"), "--install", "--source", join(dist, "release.bundle")],
  { stdio: "inherit" },
);
if (result.error) {
  if (result.error.code === "ENOENT") {
    console.error("create-switchyard: Python 3 is required (python3 not found on PATH)");
    process.exit(2);
  }
  throw result.error;
}
process.exit(result.status ?? 1);
