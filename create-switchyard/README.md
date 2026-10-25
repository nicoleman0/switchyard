# create-switchyard

Adds [Switchyard](https://github.com/nicoleman0/switchyard) to a git repo, and updates it later. It needs git, Python 3.10 or newer, and Node.js 18 or later.

- Install, from inside the repo: `npm init switchyard@latest`
- Update, on a clean branch: `npm init switchyard@latest update`
- Pass updater arguments after `--`, such as `npm init switchyard@latest update -- --to 0.7.2`.
- Preview an update without writing files: `npm init switchyard@latest update -- --dry-run`. Without the `--` it is also safe, but npm can fail with an `enoent` error on a first run.

`npx create-switchyard@latest` takes the same arguments, without the `--`. Keep `@latest`: without it, npm can run an older copy from its cache.

The package holds every release from 0.7.0 through its own version, so an update needs no access to GitHub. See the [main README](https://github.com/nicoleman0/switchyard#add-it-to-an-existing-repo) for what install and update do.
