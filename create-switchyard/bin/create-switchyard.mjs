#!/usr/bin/env node
// Runs the bundled updater against the releases bundled in dist/release.bundle.
import { spawnSync } from "node:child_process";
import { lstatSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const usage = `usage: npm init switchyard@latest                    install into this git repo
       npm init switchyard@latest update             update to the newest bundled release
       npm init switchyard@latest update -- ARGS     pass ARGS to the updater, such as --to X.Y.Z
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
  updater(["--source", bundle, ...args.slice(1)]);
}
if (args.length === 1 && (args[0] === "--help" || args[0] === "-h")) {
  console.log(usage);
  process.exit(0);
}
if (args.length > 0) {
  console.error(usage);
  process.exit(2);
}

const installed = installedVersion();
if (installed !== null) {
  console.error(`create-switchyard: switchyard/VERSION already names ${installed}; to update, run npm init switchyard@latest update`);
  process.exit(2);
}
updater(["--install", "--source", bundle]);
