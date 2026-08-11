// Social share card: adore logo centered on the brand accent background.
import sharp from "sharp";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const SIZE = 1200;
const BG = "#558184";
const LOGO = resolve(__dirname, "../public/brand/adore_logo.png");
const OUT = resolve(__dirname, "../public/brand/og-share.png");

const logoMax = Math.round(SIZE * 0.62);
const logo = await sharp(LOGO)
  .resize(logoMax, logoMax, { fit: "inside" })
  .toBuffer();
const { width = logoMax, height = logoMax } = await sharp(logo).metadata();
const left = Math.round((SIZE - width) / 2);
const top = Math.round((SIZE - height) / 2);

await sharp({
  create: {
    width: SIZE,
    height: SIZE,
    channels: 4,
    background: BG,
  },
})
  .composite([{ input: logo, left, top }])
  .png()
  .toFile(OUT);

console.log("wrote", OUT);
