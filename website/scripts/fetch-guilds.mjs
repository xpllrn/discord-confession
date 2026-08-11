#!/usr/bin/env node
/**
 * Fetch guilds across Adore / Cupid / Confess bots and write the top N
 * biggest servers into website/src/data/guilds.ts, plus icons under
 * website/public/guilds/.
 *
 * Env tokens (loaded from each bot's .env):
 *   ADORE_TOKEN / DISCORD_TOKEN  (adore-main)
 *   DISCORD_TOKEN                (cupid)
 *   DISCORD_TOKEN                (confess)
 *
 * Usage:
 *   node website/scripts/fetch-guilds.mjs
 */
import { readFileSync, writeFileSync, mkdirSync, createWriteStream, existsSync, readdirSync, unlinkSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { pipeline } from "node:stream/promises";
import { Readable } from "node:stream";

const __dirname = dirname(fileURLToPath(import.meta.url));
const WEBSITE = resolve(__dirname, "..");
const ROOT = resolve(WEBSITE, "..");
const NETWORK = resolve(ROOT, "..");
const OUT_DATA = resolve(WEBSITE, "src/data/guilds.ts");
const OUT_ICONS = resolve(WEBSITE, "public/guilds");
const LIMIT = 10;

const ENV_FILES = [
  resolve(ROOT, ".env"),
  resolve(NETWORK, "cupid/.env"),
  resolve(NETWORK, "confess/.env"),
];

function loadEnvFile(path) {
  const out = {};
  try {
    const text = readFileSync(path, "utf8");
    for (const line of text.split("\n")) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith("#")) continue;
      const eq = trimmed.indexOf("=");
      if (eq === -1) continue;
      const key = trimmed.slice(0, eq).trim();
      let val = trimmed.slice(eq + 1).trim();
      if (
        (val.startsWith('"') && val.endsWith('"')) ||
        (val.startsWith("'") && val.endsWith("'"))
      ) {
        val = val.slice(1, -1);
      }
      out[key] = val;
    }
  } catch {
    /* missing is fine */
  }
  return out;
}

function loadTokens() {
  const adoreEnv = loadEnvFile(ENV_FILES[0]);
  const cupidEnv = loadEnvFile(ENV_FILES[1]);
  const confessEnv = loadEnvFile(ENV_FILES[2]);

  const tokens = [
    ["adore", adoreEnv.ADORE_TOKEN || adoreEnv.DISCORD_TOKEN || process.env.ADORE_TOKEN || process.env.DISCORD_TOKEN],
    ["cupid", cupidEnv.DISCORD_TOKEN || process.env.CUPID_TOKEN],
    ["confess", confessEnv.DISCORD_TOKEN || process.env.CONFESS_TOKEN],
  ].filter(([, t]) => !!t);

  if (!tokens.length) {
    console.error("Missing bot tokens. Need ADORE_TOKEN and/or cupid/confess DISCORD_TOKEN in .env files.");
    process.exit(1);
  }
  return tokens;
}

mkdirSync(OUT_ICONS, { recursive: true });

function cleanName(name) {
  let s = (name || "").normalize("NFKC");
  // Prefer plain latin words for the marquee; fall back to letters/digits.
  const latin = [...s.matchAll(/[A-Za-z0-9][A-Za-z0-9'’|&.+\-]*/g)].map((m) => m[0]);
  if (latin.length) {
    s = latin.join(" ");
  } else {
    s = s.replace(/[\p{Extended_Pictographic}\p{Emoji_Component}]/gu, " ");
    s = s.replace(/[^\p{L}\p{N}\s'’|&.-]/gu, " ");
  }
  s = s.replace(/\s+/g, " ").trim().toLowerCase();
  return s || "server";
}

function iconUrl(id, icon, size = 128) {
  if (!icon) return null;
  const ext = icon.startsWith("a_") ? "gif" : "png";
  return `https://cdn.discordapp.com/icons/${id}/${icon}.${ext}?size=${size}`;
}

async function download(url, dest) {
  const res = await fetch(url);
  if (!res.ok || !res.body) throw new Error(`download ${url} → ${res.status}`);
  await pipeline(Readable.fromWeb(res.body), createWriteStream(dest));
}

async function fetchGuilds(token) {
  const guilds = [];
  let after = undefined;

  while (true) {
    const qs = new URLSearchParams({ limit: "200", with_counts: "true" });
    if (after) qs.set("after", after);
    const res = await fetch(`https://discord.com/api/v10/users/@me/guilds?${qs}`, {
      headers: { Authorization: `Bot ${token}` },
    });
    if (!res.ok) {
      const body = await res.text();
      throw new Error(`Discord API ${res.status}: ${body}`);
    }
    const batch = await res.json();
    if (!Array.isArray(batch) || batch.length === 0) break;
    guilds.push(...batch);
    if (batch.length < 200) break;
    after = batch[batch.length - 1].id;
  }

  return guilds;
}

const tokens = loadTokens();
const byId = new Map();

for (const [label, token] of tokens) {
  try {
    const guilds = await fetchGuilds(token);
    console.log(`${label}: ${guilds.length} guilds`);
    for (const g of guilds) {
      const members =
        typeof g.approximate_member_count === "number" ? g.approximate_member_count : null;
      const prev = byId.get(g.id);
      if (!prev) {
        byId.set(g.id, {
          id: g.id,
          name: g.name,
          icon: g.icon,
          members,
          bots: [label],
        });
        continue;
      }
      if (!prev.bots.includes(label)) prev.bots.push(label);
      // Keep the richest snapshot (prefer known member count + icon).
      if ((members ?? -1) > (prev.members ?? -1)) prev.members = members;
      if (!prev.icon && g.icon) prev.icon = g.icon;
      if (g.name) prev.name = g.name;
    }
  } catch (err) {
    console.warn(`${label}: failed (${err.message})`);
  }
}

const all = [...byId.values()];
all.sort((a, b) => {
  const ma = a.members ?? -1;
  const mb = b.members ?? -1;
  if (mb !== ma) return mb - ma;
  // Prefer servers with icons when tied / unknown.
  const ia = a.icon ? 1 : 0;
  const ib = b.icon ? 1 : 0;
  if (ib !== ia) return ib - ia;
  return String(a.id).localeCompare(String(b.id));
});

const selected = all.slice(0, LIMIT);
console.log("Top servers:");
for (const g of selected) {
  console.log(
    `  ${(g.members ?? 0).toLocaleString().padStart(7)}  ${cleanName(g.name)}  [${g.bots.join("+")}]`
  );
}

// Replace icon files for a clean set.
for (const file of readdirSync(OUT_ICONS)) {
  try {
    unlinkSync(resolve(OUT_ICONS, file));
  } catch {
    /* ignore */
  }
}

const rows = [];
for (const g of selected) {
  const url = iconUrl(g.id, g.icon);
  let iconPath = null;
  if (url) {
    const ext = g.icon.startsWith("a_") ? "gif" : "png";
    const file = `${g.id}.${ext}`;
    const dest = resolve(OUT_ICONS, file);
    try {
      await download(url, dest);
      iconPath = `/guilds/${file}`;
    } catch (err) {
      console.warn(`icon skip ${g.name}: ${err.message}`);
    }
  }
  rows.push({
    id: g.id,
    name: cleanName(g.name),
    icon: iconPath,
    members: typeof g.members === "number" ? g.members : null,
  });
}

const ts = `// Auto-generated by scripts/fetch-guilds.mjs - do not edit by hand.
// Top ${LIMIT} servers by approximate_member_count across Adore, Cupid, and Confess.
export type GuildShowcase = {
  id: string;
  name: string;
  icon: string | null;
  members: number | null;
};

export const guilds: GuildShowcase[] = ${JSON.stringify(rows, null, 2)};
`;

writeFileSync(OUT_DATA, ts);
console.log(`Wrote ${rows.length} guilds → ${OUT_DATA}`);
console.log(`Icons → ${OUT_ICONS}`);
