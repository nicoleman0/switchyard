#!/usr/bin/env node
// Runs the bundled updater against the releases bundled in dist/release.bundle.
import { spawnSync } from "node:child_process";
import { lstatSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const usage = `usage: npm init switchyard@latest                       install into this git repo
       npm init switchyard@latest -- --openspec        install with OpenSpec
       npm init switchyard@latest -- --no-openspec     install with plain plans
       npm init switchyard@latest -- --tracker linear   install with Linear as the tracker
       npm init switchyard@latest update                update to the newest bundled release
       npm init switchyard@latest update -- --dry-run   print the report without writing files
       npm init switchyard@latest update -- ARGS        pass ARGS to the updater, such as --to X.Y.Z
--dry-run without the -- is also safe, but npm can fail with an enoent error on a first run.
npx create-switchyard@latest takes the same arguments, without the --.`;
const args = process.argv.slice(2);
const dist = join(dirname(fileURLToPath(import.meta.url)), "..", "dist");
const bundle = join(dist, "release.bundle");

// The package decides these. argparse also accepts abbreviations such as --sou, so refuse prefixes.
const reserved = ["--source", "--install"];
const isReserved = (arg) => {
  const name = arg.split("=")[0];
  return name.startsWith("--") && name.length > 2 && reserved.some((option) => option.startsWith(name));
};

function updater(updaterArgs) {
  const result = spawnSync("python3", [join(dist, "update-switchyard.py"), ...updaterArgs], { stdio: "inherit" });
  if (result.error) {
    if (result.error.code === "ENOENT") {
      console.error("create-switchyard: Python 3 is required (python3 not found on PATH)");
      process.exit(2);
    }
    throw result.error;
  }
  process.exit(result.status ?? 1);
}

function installedVersion() {
  const top = spawnSync("git", ["rev-parse", "--show-toplevel"], { encoding: "utf8" });
  if (top.status !== 0) return null;
  const versionFile = join(top.stdout.trim(), "switchyard", "VERSION");
  try {
    if (!lstatSync(versionFile).isFile()) return null;
  } catch {
    return null;
  }
  return readFileSync(versionFile, "utf8").trim();
}

if (args[0] === "update") {
  const refused = args.slice(1).filter(isReserved);
  if (refused.length) {
    console.error(`create-switchyard: update sets --source and --install itself; remove ${refused.join(" ")}`);
    process.exit(2);
  }
  const forwarded = args.slice(1);
  // npm keeps --dry-run given without -- for itself and only sets this variable.
  if (process.env.npm_config_dry_run === "true" && !forwarded.includes("--dry-run")) forwarded.push("--dry-run");
  updater(["--source", bundle, ...forwarded]);
}
if (args.length === 1 && (args[0] === "--help" || args[0] === "-h")) {
  console.log(usage);
  process.exit(0);
}
// One OpenSpec mode flag plus --tracker <name> or --tracker=<name>, in any
// order. The updater validates the name, so forward it unvalidated.
const openspecFlags = args.filter((arg) => ["--openspec", "--no-openspec"].includes(arg));
let trackerValue = null;
let trackerNamed = false;
for (let index = 0; index < args.length; index++) {
  const arg = args[index];
  if (["--openspec", "--no-openspec"].includes(arg)) {
    continue; // counted and validated below
  }
  if (arg === "--tracker") {
    const value = args[index + 1];
    if (value === undefined || value.startsWith("--")) {
      console.error(usage);
      process.exit(2);
    }
    trackerValue = value;
    trackerNamed = true;
    index++;
  } else if (arg.startsWith("--tracker=")) {
    trackerValue = arg.slice("--tracker=".length);
    trackerNamed = true;
  } else {
    console.error(usage);
    process.exit(2);
  }
}
if (!trackerNamed) {
  // npm 11 swallows --tracker=linear without a -- into this variable.
  const value = process.env.npm_config_tracker;
  if (value !== undefined && value !== "") trackerValue = value;
}
if (openspecFlags.length > 1) {
  console.error(usage);
  process.exit(2);
}

const installed = installedVersion();
if (installed !== null) {
  console.error(`create-switchyard: switchyard/VERSION already names ${installed}; to update, run npm init switchyard@latest update`);
  process.exit(2);
}
// npm 11 exports an empty value for a swallowed --no-openspec.
const npmFlags = new Map([
  ["true", "--openspec"], ["false", "--no-openspec"], ["", "--no-openspec"],
]);
const flag = openspecFlags[0] ?? npmFlags.get(process.env.npm_config_openspec);
updater(["--install", "--source", bundle,
  ...(flag ? [flag] : []), ...(trackerValue !== null ? ["--tracker", trackerValue] : [])]);
