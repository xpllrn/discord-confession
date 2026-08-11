# confess.adore.rest

Marketing site for **confession**. Astro static site for **Cloudflare Pages** — same setup as adore.rest/`website`.

## Develop

```bash
npm install
npm run dev
```

## Build

```bash
npm run build   # outputs to ./dist
```

## Cloudflare Pages (Git)

In the Cloudflare dashboard → Workers & Pages → this project → Settings → Builds:

- **Root directory:** `website`
- **Framework preset:** Astro (or None)
- **Build command:** `npm run build`
- **Build output directory:** `dist`
- **Deploy command:** leave empty (do **not** use `npx wrangler deploy`)

Optional CLI deploy:

```bash
npm run build
npx wrangler pages deploy dist --project-name=confession
```
