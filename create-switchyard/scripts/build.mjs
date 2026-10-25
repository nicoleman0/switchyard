// Builds dist/: a git bundle of every release from OLDEST_RELEASE on, plus a copy of the updater.
// Runs as `prepack`. Reads older releases from their tags and the packed one from the
// working tree's tracked files. Never writes to the repo.
import { execFileSync } from "node:child_process";
import { copyFileSync, lstatSync, mkdirSync, mkdtempSync, readFileSync, rmSync, statSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

// The oldest base release the updater accepts.
const OLDEST_RELEASE = "0.7.0";

const pkgDir = resolve(dirname(fileURLToPath(import.meta.url)), "..");

function fail(message) {
  console.error(`create-switchyard build: ${message}`);
  process.exit(1);
}

function git(cwd, args, options = {}) {
  return execFileSync("git", args, { cwd, encoding: "utf8", maxBuffer: 64 * 1024 * 1024, ...options });
}

const parseVersion = (text) => text.split(".").map(Number);
const compareVersions = (a, b) => {
  const [x, y] = [parseVersion(a), parseVersion(b)];
  for (let i = 0; i < 3; i++) if (x[i] !== y[i]) return x[i] - y[i];
  return 0;
};

const parsePaths = (text) =>
  text.split("\n").map((line) => line.trim()).filter((line) => line && !line.startsWith("#"));

const root = git(pkgDir, ["rev-parse", "--show-toplevel"]).trim();
const version = readFileSync(join(root, "switchyard/VERSION"), "utf8").trim();
if (!/^\d+\.\d+\.\d+$/.test(version)) fail(`switchyard/VERSION is "${version}", not X.Y.Z`);
const pkgVersion = JSON.parse(readFileSync(join(pkgDir, "package.json"), "utf8")).version;
if (pkgVersion !== version) fail(`package.json is ${pkgVersion}; switchyard/VERSION is ${version}`);

// Same heading format as the CI release-version check.
const changelog = readFileSync(join(root, "CHANGELOG.md"), "utf8");
const older = [...changelog.matchAll(/^## \[(\d+\.\d+\.\d+)\] - /gm)]
  .map((match) => match[1])
  .filter((release) => compareVersions(release, OLDEST_RELEASE) >= 0 && compareVersions(release, version) < 0)
  .sort(compareVersions);

for (const release of older) {
  const tag = `v${release}`;
  try {
    git(root, ["rev-parse", "--quiet", "--verify", `refs/tags/${tag}^{commit}`], { stdio: "pipe" });
  } catch {
    fail(`tag ${tag} is missing; fetch release tags with \`git fetch --tags\` (a shallow clone has none)`);
  }
  const tagged = git(root, ["show", `${tag}:switchyard/VERSION`]).trim();
  if (tagged !== release) fail(`tag ${tag} has switchyard/VERSION ${tagged}`);
}

// The updater filters the base by the target's path list, so every release carries the union.
const pathSets = [
  ...older.map((release) => parsePaths(git(root, ["show", `v${release}:switchyard/update-paths.txt`]))),
  parsePaths(readFileSync(join(root, "switchyard/update-paths.txt"), "utf8")),
];
const paths = [...new Set(pathSets.flat())].sort();

// Each entry: { path, mode: "100644" | "100755", content: Buffer }.
function taggedEntries(release) {
  const listing = git(root, ["ls-tree", "-r", "-z", `v${release}`, "--", ...paths]);
  return listing.split("\0").filter(Boolean).map((line) => {
    const [meta, path] = line.split("\t");
    const [mode, type, sha] = meta.split(" ");
    if (type !== "blob" || (mode !== "100644" && mode !== "100755")) fail(`v${release}:${path} is not a regular file (mode ${mode})`);
    return { path, mode, content: execFileSync("git", ["cat-file", "blob", sha], { cwd: root, maxBuffer: 64 * 1024 * 1024 }) };
  });
}

function workingTreeEntries() {
  const listing = git(root, ["ls-files", "-s", "-z", "--", ...paths]);
  return listing.split("\0").filter(Boolean).map((line) => {
    const [meta, path] = line.split("\t");
    const indexMode = meta.split(" ")[0];
    if (indexMode !== "100644" && indexMode !== "100755") fail(`${path} is not a regular file (mode ${indexMode})`);
    const full = join(root, path);
    let info;
    try {
      info = lstatSync(full);
    } catch {
      fail(`tracked file missing from the working tree: ${path}`);
    }
    if (!info.isFile()) fail(`${path} is not a regular file in the working tree`);
    return { path, mode: statSync(full).mode & 0o100 ? "100755" : "100644", content: readFileSync(full) };
  });
}

const releases = [...older.map((release) => ({ release, entries: taggedEntries(release) })),
  { release: version, entries: workingTreeEntries() }];
for (const { release, entries } of releases) {
  if (entries.length === 0) fail(`v${release} has no files under the paths in update-paths.txt`);
  let content;
  try {
    content = release === version
      ? readFileSync(join(root, "CHANGELOG.md"))
      : execFileSync("git", ["show", `v${release}:CHANGELOG.md`], { cwd: root, maxBuffer: 64 * 1024 * 1024 });
  } catch {
    fail(`v${release} has no CHANGELOG.md`);
  }
  if (!new RegExp(`^## \\[${release.replaceAll(".", "\\.")}\\] - `, "m").test(content.toString("utf8"))) {
    fail(`CHANGELOG.md for v${release} has no ## [${release}] - heading`);
  }
  entries.push({ path: "CHANGELOG.md", mode: "100644", content });
}

const work = mkdtempSync(join(tmpdir(), "create-switchyard-"));
let bundleSize;
try {
  const identity = { GIT_AUTHOR_NAME: "Switchyard", GIT_AUTHOR_EMAIL: "switchyard@localhost", GIT_COMMITTER_NAME: "Switchyard", GIT_COMMITTER_EMAIL: "switchyard@localhost" };
  const env = { ...process.env, ...identity, GIT_CONFIG_NOSYSTEM: "1", GIT_CONFIG_GLOBAL: "/dev/null", GIT_INDEX_FILE: join(work, "index") };
  const run = (args, input, runEnv = env) => git(work, args, { env: runEnv, input, stdio: ["pipe", "pipe", "pipe"] }).trim();
  run(["init", "-q", "--bare", "-b", "main", "repo.git"]);
  const repo = (args, input, runEnv = env) => run(["--git-dir", join(work, "repo.git"), ...args], input, runEnv);

  let parent;
  for (const { release, entries } of releases) {
    rmSync(join(work, "index"), { force: true });
    const indexInfo = entries
      .map(({ path, mode, content }) => `${mode} ${repo(["hash-object", "-w", "--stdin"], content)}\t${path}\0`)
      .join("");
    repo(["update-index", "--add", "-z", "--index-info"], indexInfo);
    const tree = repo(["write-tree"]);
    const revision = release === version ? "HEAD" : `v${release}^{commit}`;
    const date = git(root, ["show", "-s", "--format=%cI", revision]).trim();
    // Fixed dates keep the bundle tied to its source revisions across builds.
    const commitEnv = { ...env, GIT_AUTHOR_DATE: date, GIT_COMMITTER_DATE: date };
    const commit = repo(["commit-tree", tree, ...(parent ? ["-p", parent] : []), "-m", `Switchyard ${release}`], undefined, commitEnv);
    repo(["tag", `v${release}`, commit]);
    parent = commit;
  }
  repo(["update-ref", "refs/heads/main", parent]);

  const dist = join(pkgDir, "dist");
  rmSync(dist, { recursive: true, force: true });
  mkdirSync(dist);
  const bundle = join(dist, "release.bundle");
  repo(["bundle", "create", "-q", bundle, "main", ...releases.map(({ release }) => `v${release}`)]);
  bundleSize = statSync(bundle).size;
  copyFileSync(join(root, "switchyard/scripts/update-switchyard.py"), join(dist, "update-switchyard.py"));
} finally {
  rmSync(work, { recursive: true, force: true });
}
const range = releases.length > 1 ? `v${releases[0].release} through v${version}` : `v${version}`;
console.log(`create-switchyard build: ${releases.length} releases, ${range}, bundle ${bundleSize} bytes`);
