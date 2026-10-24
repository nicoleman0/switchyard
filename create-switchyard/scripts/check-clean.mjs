// Runs as `prepublishOnly`: a published package must match a commit.
import { execFileSync } from "node:child_process";

const status = execFileSync("git", ["status", "--porcelain"], { encoding: "utf8" }).trim();
if (status) {
  console.error("create-switchyard: refusing to publish with uncommitted changes:\n" + status);
  process.exit(1);
}
