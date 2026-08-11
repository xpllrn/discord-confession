# adore.rest - website

Marketing site for the **adore** Discord bot. Built with [Astro](https://astro.build)
(static output) and [Tailwind CSS v4](https://tailwindcss.com), designed to deploy on
**Cloudflare Pages**.

## Stack

- **Astro 6** - static site generation, zero JS by default
- **Tailwind CSS v4** - via the `@tailwindcss/vite` plugin (theme tokens in `src/styles/global.css`)
- **TypeScript** - content/config in `src/data/site.ts`

## Develop

```bash
npm install
npm run dev      # http://localhost:4321
```

## Build

```bash
npm run build    # outputs to ./dist
npm run preview  # preview the production build locally
```

## Project structure

```
public/                 Static assets (brand images, robots, _headers, _redirects, sitemap)
src/
  components/           Reusable .astro components (Nav, Hero, Features, CommandExplorer, …)
  data/site.ts          Single source of truth: links, stats, features, commands, plans, faqs
  layouts/Layout.astro  Base HTML shell (SEO meta, fonts, scripts)
  pages/                Routes: index, features, commands, premium, 404
  styles/global.css     Tailwind import + @theme design tokens
DESIGN.md               Design system reference (colors, type, components, build notes)
```

## Configuration

Edit `src/data/site.ts` to update real links before launch:

- `invite` - your bot's OAuth2 invite URL (replace `YOUR_CLIENT_ID`)
- `support` - support server invite
- `dashboard`, `docs`, `github` - your real URLs
- `stats` - live server/member/command counts

Also update `public/_redirects` shortlinks to match.

## Deploy to Cloudflare Pages

This is a static Astro site, so no adapter is needed.

**Option A - Git integration (recommended)**

1. Push this repo to GitHub/GitLab.
2. In the Cloudflare dashboard: **Workers & Pages → Create → Pages → Connect to Git**.
3. Set the build configuration:
   - **Framework preset:** Astro
   - **Build command:** `npm run build`
   - **Build output directory:** `dist`
   - **Root directory:** `website` (if the repo root is the bot project)
4. Deploy, then add the custom domain `adore.rest` under **Custom domains**.

**Option B - Wrangler CLI**

```bash
npm run build
npx wrangler pages deploy dist --project-name=adore
```

`public/_headers` and `public/_redirects` are picked up automatically by Cloudflare Pages.
