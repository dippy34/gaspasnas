#!/usr/bin/env node
/**
 * Cloudflare Pages build: copy site into dist/ but exclude assets over 25 MiB.
 * Pages allows max 25 MiB per file. Exclude Escape Road folders that contain
 * oversized .wasm.unityweb files so the deploy succeeds.
 *
 * In Cloudflare Pages: set Build command to "node scripts/pages-build.js"
 * and Build output directory to "dist".
 */

const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const OUT = path.join(ROOT, 'dist');
const MAX_BYTES = 25 * 1024 * 1024; // 25 MiB

// Folders under non-semag/ that contain files >25MB (omit from deploy)
const EXCLUDE_DIRS = new Set([
  path.join(ROOT, 'non-semag', 'EscapeRoad'),
  path.join(ROOT, 'non-semag', 'EscapeRoad2'),
  path.join(ROOT, 'non-semag', 'EscapeRoadCity'),
]);

const IGNORE = new Set(['node_modules', '.git', 'dist', 'scripts']);

function shouldExclude(abs) {
  const normalized = path.normalize(abs);
  for (const d of EXCLUDE_DIRS) {
    if (normalized === d || normalized.startsWith(d + path.sep)) return true;
  }
  return false;
}

function copyRecurse(src, dest) {
  const stat = fs.statSync(src);
  if (stat.isDirectory()) {
    if (!fs.existsSync(dest)) fs.mkdirSync(dest, { recursive: true });
    for (const name of fs.readdirSync(src)) {
      if (IGNORE.has(name)) continue;
      const s = path.join(src, name);
      const d = path.join(dest, name);
      if (shouldExclude(s)) continue;
      copyRecurse(s, d);
    }
  } else {
    const dir = path.dirname(dest);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    fs.copyFileSync(src, dest);
  }
}

if (fs.existsSync(OUT)) fs.rmSync(OUT, { recursive: true });
fs.mkdirSync(OUT, { recursive: true });

// Copy root contents into dist (not root itself)
for (const name of fs.readdirSync(ROOT)) {
  if (IGNORE.has(name)) continue;
  const s = path.join(ROOT, name);
  const d = path.join(OUT, name);
  if (shouldExclude(s)) continue;
  copyRecurse(s, d);
}
console.log('Pages build output written to dist/ (EscapeRoad, EscapeRoad2, EscapeRoadCity excluded).');

