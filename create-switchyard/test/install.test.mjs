// Packs the package and runs the tarball against scratch git repos.
import assert from "node:assert/strict";
import { execFileSync, spawnSync } from "node:child_process";
import { copyFileSync, existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, statSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { after, before, test } from "node:test";
import { fileURLToPath } from "node:url";

const pkgDir = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const version = JSON.parse(readFileSync(join(pkgDir, "package.json"), "utf8")).version;
const tmp = mkdtempSync(join(tmpdir(), "create-switchyard-test-"));
const gitEnv = {
  ...process.env,
  GIT_AUTHOR_NAME: "Test User", GIT_AUTHOR_EMAIL: "test@example.com",
  GIT_COMMITTER_NAME: "Test User", GIT_COMMITTER_EMAIL: "test@example.com",
  GIT_CONFIG_NOSYSTEM: "1", GIT_CONFIG_GLOBAL: "/dev/null",
  npm_config_cache: join(tmp, "npm-cache"),
};
const repo = join(tmp, "project");
const bundleGit = join(tmp, "bundle.git");
let tarball;

const gitIn = (cwd, ...args) => execFileSync("git", args, { cwd, env: gitEnv, encoding: "utf8", stdio: "pipe" });
const git = (...args) => gitIn(repo, ...args);
const createIn = (cwd, ...args) =>
  spawnSync("npm", ["exec", "--yes", `--package=${tarball}`, "--", "create-switchyard", ...args], {
    cwd, env: gitEnv, encoding: "utf8",
  });
const create = (...args) => createIn(repo, ...args);
const output = (result) => result.stdout + result.stderr;

// Releases from 0.7.0 through the package version, as the CHANGELOG headings name them.
const root = resolve(pkgDir, "..");
const cmp = (a, b) => {
  const [x, y] = [a, b].map((v) => v.split(".").map(Number));
  return x[0] - y[0] || x[1] - y[1] || x[2] - y[2];
};
const expectedReleases = [...readFileSync(join(root, "CHANGELOG.md"), "utf8").matchAll(/^## \[(\d+\.\d+\.\d+)\] - /gm)]
  .map((match) => match[1])
  .filter((release) => cmp(release, "0.7.0") >= 0 && cmp(release, version) <= 0)
  .sort(cmp);

// A committed repo holding one bundled release's tree.
function releaseRepo(name, release) {
  const dir = join(tmp, name);
  mkdirSync(dir);
  gitIn(dir, "init", "-q", "-b", "main");
  const archive = execFileSync("git", ["--git-dir", bundleGit, "archive", `v${release}`], { env: gitEnv });
  execFileSync("tar", ["-x", "-C", dir], { input: archive });
  gitIn(dir, "add", "-A");
  gitIn(dir, "commit", "-qm", `switchyard ${release}`);
  return dir;
}

before(() => {
  execFileSync("npm", ["pack", "--pack-destination", tmp], { cwd: pkgDir, env: gitEnv, stdio: "pipe" });
  tarball = join(tmp, `create-switchyard-${version}.tgz`);
  const unpacked = join(tmp, "unpacked");
  mkdirSync(unpacked);
  execFileSync("tar", ["-xzf", tarball, "-C", unpacked]);
  execFileSync("git", ["clone", "-q", "--bare", join(unpacked, "package/dist/release.bundle"), bundleGit], { env: gitEnv, stdio: "pipe" });
  mkdirSync(repo);
  git("init", "-q", "-b", "main");
  writeFileSync(join(repo, "app.txt"), "app\n");
  git("add", "-A");
  git("commit", "-qm", "init");
});

after(() => rmSync(tmp, { recursive: true, force: true }));

test("the bundle holds every release from 0.7.0 through the package version", () => {
  assert.ok(expectedReleases.includes("0.7.0") && expectedReleases.includes(version), expectedReleases.join(", "));
  const tags = gitIn(tmp, "--git-dir", bundleGit, "tag", "--list", "v*").split("\n").filter(Boolean).map((t) => t.slice(1)).sort(cmp);
  assert.deepEqual(tags, expectedReleases);
  assert.equal(gitIn(tmp, "--git-dir", bundleGit, "rev-parse", "main").trim(), gitIn(tmp, "--git-dir", bundleGit, "rev-parse", `v${version}^{commit}`).trim());
  for (const release of expectedReleases) {
    const changelog = gitIn(tmp, "--git-dir", bundleGit, "show", `v${release}:CHANGELOG.md`);
    assert.match(changelog, new RegExp(`^## \\[${release.replaceAll(".", "\\.")}\\] - `, "m"), `v${release}`);
  }
});

test("installs the bundled release into a git repo", () => {
  const result = create();
  assert.equal(result.status, 0, output(result));
  assert.equal(readFileSync(join(repo, "switchyard/VERSION"), "utf8").trim(), version);
  assert.match(readFileSync(join(repo, ".gitignore"), "utf8"), /^\.switchyard\/$/m);
  assert.ok(statSync(join(repo, "switchyard/hooks/worktree-up.sh")).mode & 0o111, "hook is executable");
  assert.ok(!existsSync(join(repo, "create-switchyard")), "package folder reached the project");
  assert.ok(!existsSync(join(repo, "CHANGELOG.md")), "package changelog reached the project");
});

test("a second run refuses and names the update command", () => {
  git("add", "-A");
  git("commit", "-qm", "switchyard");
  const result = create();
  assert.equal(result.status, 2, output(result));
  assert.match(result.stderr, new RegExp(`already names ${version.replaceAll(".", "\\.")}; to update, run npm init switchyard@latest update`));
});

test("--help exits 0", () => {
  const result = create("--help");
  assert.equal(result.status, 0);
  assert.match(result.stdout, /usage/);
});

test("an unknown argument exits 2", () => {
  const result = create("install");
  assert.equal(result.status, 2);
  assert.match(result.stderr, /usage/);
});

test("install outside a git repo reports the updater's refusal", () => {
  const dir = join(tmp, "not-a-repo");
  mkdirSync(dir);
  const result = createIn(dir);
  assert.equal(result.status, 2, output(result));
  assert.match(result.stderr, /run this command inside a git work tree/);
});

test("update takes an older release to the package version, then reports it is current", () => {
  const dir = releaseRepo("from-0.7.2", "0.7.2");
  let result = createIn(dir, "update");
  assert.equal(result.status, 0, output(result));
  assert.match(result.stdout, /^updated: /m);
  assert.match(result.stdout, new RegExp(`Release notes, 0\\.7\\.2 to ${version.replaceAll(".", "\\.")}:`));
  assert.match(result.stdout, new RegExp(`^## \\[${version.replaceAll(".", "\\.")}\\] - `, "m"));
  assert.doesNotMatch(result.stdout, /^## \[0\.7\.2\] - /m);
  assert.doesNotMatch(result.stdout, /^## \[Unreleased\]$/m);
  assert.equal(readFileSync(join(dir, "switchyard/VERSION"), "utf8").trim(), version);
  gitIn(dir, "add", "-A");
  gitIn(dir, "commit", "-qm", "update");
  result = createIn(dir, "update");
  assert.equal(result.status, 0, output(result));
  assert.match(result.stdout, new RegExp(`Already at ${version.replaceAll(".", "\\.")}`));
});

test("update forwards other arguments to the updater", () => {
  const dir = releaseRepo("forward", "0.7.2");
  const result = createIn(dir, "update", "--to", "0.7.2");
  assert.equal(result.status, 0, output(result));
  assert.match(result.stdout, /Already at 0\.7\.2/);
});

test("update forwards npm's swallowed --dry-run and writes nothing", () => {
  const dir = releaseRepo("dry-run", "0.7.2");
  const result = spawnSync("npm", ["exec", "--yes", `--package=${tarball}`, "--", "create-switchyard", "update"], {
    cwd: dir, env: { ...gitEnv, npm_config_dry_run: "true" }, encoding: "utf8",
  });
  assert.equal(result.status, 0, output(result));
  assert.match(result.stdout, /^Dry run: nothing was written\.$/m);
  assert.equal(gitIn(dir, "status", "--porcelain"), "");
  assert.equal(readFileSync(join(dir, "switchyard/VERSION"), "utf8").trim(), "0.7.2");
});

test("update refuses --source and --install in any form", () => {
  const dir = releaseRepo("refused", "0.7.2");
  for (const args of [["--source", "x"], ["--source=x"], ["--inst"], ["--install"]]) {
    const result = createIn(dir, "update", ...args);
    assert.equal(result.status, 2, `${args.join(" ")}: ${output(result)}`);
    assert.match(result.stderr, /update sets --source and --install itself/);
    assert.equal(gitIn(dir, "status", "--porcelain"), "", args.join(" "));
    assert.equal(readFileSync(join(dir, "switchyard/VERSION"), "utf8").trim(), "0.7.2");
  }
});

test("update marks a local edit that conflicts with the release", () => {
  const dir = releaseRepo("conflict", "0.7.2");
  const changed = gitIn(tmp, "--git-dir", bundleGit, "diff", "--name-only", "v0.7.2", "main")
    .split("\n")
    .filter((path) => path && path !== "switchyard/VERSION" && path !== "switchyard/routing.md");
  assert.ok(changed.length > 0, "no file changed between 0.7.2 and the package version");
  writeFileSync(join(dir, changed[0]), "a local edit\n");
  gitIn(dir, "commit", "-qam", "local edit");
  const result = createIn(dir, "update");
  assert.equal(result.status, 1, output(result));
  assert.match(result.stdout, new RegExp(`^conflict: ${changed[0].replaceAll(".", "\\.")}$`, "m"));
  assert.match(readFileSync(join(dir, changed[0]), "utf8"), /^<<<<<<< /m);
});

test("the build fails in a clone without release tags", () => {
  const clone = join(tmp, "shallow");
  execFileSync("git", ["clone", "-q", "--depth", "1", "--no-tags", `file://${root}`, clone], { env: gitEnv });
  copyFileSync(join(pkgDir, "scripts/build.mjs"), join(clone, "create-switchyard/scripts/build.mjs"));
  const result = spawnSync("node", [join(clone, "create-switchyard/scripts/build.mjs")], { env: gitEnv, encoding: "utf8" });
  assert.equal(result.status, 1, output(result));
  assert.match(result.stderr, /tag v\d+\.\d+\.\d+ is missing; fetch release tags/);
  assert.ok(!existsSync(join(clone, "create-switchyard/dist")), "dist/ was written");
});
