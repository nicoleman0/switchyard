// Captures each route in light and dark at 1280px and 390px.
// From the worktree root, with the dev server running:
//   SHOTS_BASE=http://127.0.0.1:<port> node switchyard/scripts/shots.mjs <out-dir>
// Needs @playwright/test in the package at SHOTS_PACKAGE_DIR (default: the worktree root).
// The preflight probe in preflight.sh uses the same package lookup.
import { createRequire } from 'node:module'
import { mkdirSync } from 'node:fs'
import path from 'node:path'

// Project: list the screens a reviewer should see, as [shot name, path].
const routes = [['home', '/']]

const base = process.env.SHOTS_BASE ?? 'http://127.0.0.1:3000'
const require = createRequire(path.resolve(process.env.SHOTS_PACKAGE_DIR ?? '.', 'package.json'))
const { chromium } = require('@playwright/test')
const out = process.argv[2]
if (!out) throw new Error('Usage: shots.mjs <out-dir>')
mkdirSync(out, { recursive: true })

const browser = await chromium.launch()
for (const scheme of ['light', 'dark']) {
  for (const [vp, size] of [['desktop', { width: 1280, height: 860 }], ['phone', { width: 390, height: 844 }]]) {
    const ctx = await browser.newContext({ colorScheme: scheme, viewport: size, reducedMotion: 'reduce' })
    const page = await ctx.newPage()
    // Project: sign in here if the app needs it.
    for (const [name, route] of routes) {
      await page.goto(base + route)
      await page.waitForLoadState('networkidle')
      await page.screenshot({ path: path.join(out, `${name}-${vp}-${scheme}.png`), fullPage: true })
    }
    await ctx.close()
  }
}
await browser.close()
