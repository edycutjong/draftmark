// Writes public/version.json for the static landing and deck: the release tag the Deploy workflow passes
// (NEXT_PUBLIC_APP_VERSION), else package.json's version. Runs as `prebuild`.
import { readFileSync, writeFileSync } from "node:fs";

const pkg = JSON.parse(readFileSync(new URL("../package.json", import.meta.url), "utf8"));
const version = process.env.NEXT_PUBLIC_APP_VERSION || `v${pkg.version}`;
writeFileSync(new URL("../public/version.json", import.meta.url), JSON.stringify({ version }) + "\n");
console.log(`version.json: ${version}`);
