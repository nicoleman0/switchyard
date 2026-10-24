// Packs the package and runs the tarball against a scratch git repo.
import assert from "node:assert/strict";
import { execFileSync, spawnSync } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, statSync, writeFileSync } from "node:fs";
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
let tarball;

const git = (...args) => execFileSync("git", args, { cwd: repo, env: gitEnv, stdio: "pipe" });
const create = (...args) =>
  spawnSync("npm", ["exec", "--yes", `--package=${tarball}`, "--", "create-switchyard", ...args], {
    cwd: repo, env: gitEnv, encoding: "utf8",
  });

before(() => {
  execFileSync("npm", ["pack", "--pack-destination", tmp], { cwd: pkgDir, env: gitEnv, stdio: "pipe" });
  tarball = join(tmp, `create-switchyard-${version}.tgz`);
  mkdirSync(repo);
  git("init", "-q", "-b", "main");
  writeFileSync(join(repo, "app.txt"), "app\n");
  git("add", "-A");
  git("commit", "-qm", "init");
});

after(() => rmSync(tmp, { recursive: true, force: true }));

test("installs the bundled release into a git repo", () => {
  const result = create();
  assert.equal(result.status, 0, result.stdout + result.stderr);
  assert.equal(readFileSync(join(repo, "switchyard/VERSION"), "utf8").trim(), version);
  assert.match(readFileSync(join(repo, ".gitignore"), "utf8"), /^\.switchyard\/$/m);
  assert.ok(statSync(join(repo, "switchyard/hooks/worktree-up.sh")).mode & 0o111, "hook is executable");
  assert.ok(!existsSync(join(repo, "create-switchyard")), "package folder reached the project");
});

test("a second run refuses", () => {
  git("add", "-A");
  git("commit", "-qm", "switchyard");
  const result = create();
  assert.equal(result.status, 2, result.stdout + result.stderr);
  assert.match(result.stdout + result.stderr, /already names/);
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
