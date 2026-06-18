import { existsSync, readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { gzipSync } from "node:zlib";

const BUDGET = 250 * 1024;
const dist = "dist/assets";

if (!existsSync(dist)) {
  console.error(`[check-bundle-size] ${dist} not found. Run "npm run build" first.`);
  process.exit(2);
}

const files = readdirSync(dist).filter((f) => /\.(js|css)$/.test(f));
let total = 0;
for (const file of files) {
  const buf = readFileSync(join(dist, file));
  const gz = gzipSync(buf);
  console.log(`  ${file}: ${(gz.length / 1024).toFixed(1)} KB gz`);
  total += gz.length;
}

console.log(
  `\nTotal: ${(total / 1024).toFixed(1)} KB gz / ${(BUDGET / 1024).toFixed(0)} KB budget`,
);

if (total > BUDGET) {
  console.error(
    `\n[FAIL] Initial bundle exceeds budget by ${((total - BUDGET) / 1024).toFixed(1)} KB`,
  );
  process.exit(1);
}

console.log("[OK] Within budget");
