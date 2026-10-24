// Builds dist/: a git bundle of one release plus a copy of the updater.
// Runs as `prepack`. Reads tracked files from the working tree, never writes to the repo.
import { execFileSync } from "node:child_process";
import { chmodSync, copyFileSync, existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, statSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const pkgDir = resolve(dirname(fileURLToPath(import.meta.url)), "..");

function fail(message) {
  console.error(`create-switchyard build: ${message}`);
  process.exit(1);
}

function git(cwd, args, options = {}) {
  return execFileSync("git", args, { cwd, encoding: "utf8", ...options });
}

const root = git(pkgDir, ["rev-parse", "--show-toplevel"]).trim();
const version = readFileSync(join(root, "switchyard/VERSION"), "utf8").trim();
if (!/^\d+\.\d+\.\d+$/.test(version)) fail(`switchyard/VERSION is "${version}", not X.Y.Z`);
const pkgVersion = JSON.parse(readFileSync(join(pkgDir, "package.json"), "utf8")).version;
if (pkgVersion !== version) fail(`package.json is ${pkgVersion}; switchyard/VERSION is ${version}`);

const paths = readFileSync(join(root, "switchyard/update-paths.txt"), "utf8")
  .split("\n")
  .map((line) => line.trim())
  .filter((line) => line && !line.startsWith("#"));
const files = git(root, ["ls-files", "-z", "--", ...paths]).split("\0").filter(Boolean);
if (files.length === 0) fail("no tracked files under the paths in update-paths.txt");
const missing = files.filter((file) => !existsSync(join(root, file)));
if (missing.length) fail(`tracked files missing from the working tree: ${missing.join(", ")}`);

const work = mkdtempSync(join(tmpdir(), "create-switchyard-"));
try {
  for (const file of files) {
    const target = join(work, file);
    mkdirSync(dirname(target), { recursive: true });
    copyFileSync(join(root, file), target);
    chmodSync(target, statSync(join(root, file)).mode & 0o777);
  }
  const identity = { GIT_AUTHOR_NAME: "Switchyard", GIT_AUTHOR_EMAIL: "switchyard@localhost", GIT_COMMITTER_NAME: "Switchyard", GIT_COMMITTER_EMAIL: "switchyard@localhost" };
  const env = { ...process.env, ...identity, GIT_CONFIG_NOSYSTEM: "1", GIT_CONFIG_GLOBAL: "/dev/null" };
  const run = (args) => git(work, args, { env, stdio: ["ignore", "pipe", "pipe"] });
  run(["init", "-q", "-b", "main"]);
  run(["add", "-A", "-f"]);
  run(["commit", "-q", "-m", `Switchyard ${version}`]);
  run(["tag", `v${version}`]);

  const dist = join(pkgDir, "dist");
  rmSync(dist, { recursive: true, force: true });
  mkdirSync(dist);
  run(["bundle", "create", join(dist, "release.bundle"), "main", `v${version}`]);
  copyFileSync(join(root, "switchyard/scripts/update-switchyard.py"), join(dist, "update-switchyard.py"));
} finally {
  rmSync(work, { recursive: true, force: true });
}
console.log(`create-switchyard build: ${files.length} files, v${version}`);
