# DESIGN.md: adore.rest

## Source
- Target brand: **adore** - multipurpose Discord bot (discord.py)
- Domain: adore.rest
- Capture date: 2026-06-01
- Competitor reference (structure only, NOT design): https://bleed.bot/ ("Meet the leading bot for management and engagement")
- Evidence: adore README feature list, brand assets in `adore-asset/media/`, competitor site/docs structure research.

## Design Summary
adore is a feature-rich Discord bot covering moderation, security (anti-nuke/anti-raid),
economy, social integrations (Spotify, Last.fm, Twitter, TikTok, GitHub), leveling,
tickets, AI, and deep customization. The site should feel **premium, modern, and warm** -
leaning into the "adore" name with a soft rose/blush accent over a near-black canvas.

## Design Tokens

### Colors
Dark-first palette. Defined as CSS custom properties / Tailwind `@theme` tokens.

- `--color-bg`: `#0a0a0f` (near-black base)
- `--color-bg-soft`: `#101018` (raised surfaces)
- `--color-surface`: `#16161f` (cards)
- `--color-surface-2`: `#1d1d29` (hover / nested)
- `--color-border`: `#262633` (hairline borders)
- `--color-text`: `#f5f3f7` (primary text)
- `--color-muted`: `#a3a0ad` (secondary text)
- `--color-faint`: `#6b6878` (tertiary / captions)
- Accent (rose/blush, the "adore" signature):
  - `--color-primary`: `#ff5d8f` (rose 500 - primary CTA, links, glow)
  - `--color-primary-soft`: `#ff89ab`
  - `--color-primary-deep`: `#e23e72`
- Secondary accent (violet, for gradients/variety):
  - `--color-accent`: `#a070ff`
- States: success `#3ddc97`, warning `#ffcf5c`, danger `#ff5c5c`

Gradients:
- Brand gradient: `linear-gradient(135deg, #ff5d8f 0%, #a070ff 100%)`
- Hero glow: radial rose/violet bloom behind hero headline, low opacity.

### Typography
- Display / headings: **"Geist"** or system fallback; tight tracking, large weights (600–700).
- Body: **"Inter"** with system fallback.
- Fallback stack: `ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif`.
- Mono (commands, prefixes): `"Geist Mono", ui-monospace, "SF Mono", Menlo, monospace`.
- Type scale (clamp-based, responsive):
  - Hero h1: `clamp(2.75rem, 6vw, 5rem)`, weight 700, line-height 1.02
  - Section h2: `clamp(2rem, 3.5vw, 3rem)`, weight 650
  - Card h3: `1.25rem`, weight 600
  - Body: `1rem`–`1.125rem`, line-height 1.6, color muted
  - Caption/eyebrow: `0.8125rem`, uppercase, letter-spacing `0.08em`, color primary

### Spacing And Layout
- Container max-width: `1200px`, side padding `1.25rem` (mobile) → `2rem` (desktop).
- Section vertical rhythm: `6rem`–`8rem` top/bottom on desktop, `4rem` mobile.
- Grid gaps: `1.5rem` standard, `1rem` dense.
- Radius: cards `1rem` (16px), buttons `0.75rem`, pills `9999px`.
- Shadows: soft elevation `0 8px 30px rgba(0,0,0,0.35)`; glow `0 0 40px rgba(255,93,143,0.25)`.
- Borders: 1px hairline using `--color-border`, brighten to primary on hover.

## Components
- **Nav**: sticky, translucent (backdrop-blur), logo left, links center, "Add to Discord" + "Dashboard" CTA right. Collapses to a mobile menu.
- **Buttons**:
  - Primary: brand gradient fill, white text, rounded-xl, subtle glow on hover, scale 1.02.
  - Secondary: surface bg, hairline border, text primary, border→primary on hover.
  - Ghost: transparent, muted text → text on hover.
- **Cards**: surface bg, hairline border, 16px radius, icon chip top-left (gradient bg), title + description; lift + border glow on hover.
- **Stat counters**: large gradient number + label (servers, users, commands, uptime).
- **Feature rows**: alternating image/text or icon grid.
- **Command preview**: mono chips with prefix, copy-to-clipboard, category tabs.
- **Integration logos**: Spotify, Last.fm, Twitter/X, TikTok, GitHub in a logo strip.
- **Pricing/Premium**: two-tier cards (Free vs Premium), feature checklist.
- **FAQ**: accordion.
- **Footer**: multi-column (Product, Resources, Community, Legal), logo, socials, copyright.

## Page Patterns
Section order on landing (`/`):
1. Nav
2. Hero - eyebrow, headline, subcopy, dual CTA, trust stats row, glow + floating UI mock.
3. Logo / integration strip ("Plays well with").
4. Stats band (servers, users, commands run, uptime).
5. Feature grid - 8–9 category cards (Moderation, Security, Economy, Social, Utility, Leveling, Tickets, AI, Customization).
6. Spotlight rows - 2–3 deep-dive features (Anti-Nuke, Economy/games, Social integrations) with mock visuals.
7. Commands explorer preview - tabbed categories with example commands.
8. Premium / pricing.
9. FAQ accordion.
10. Final CTA band ("Add adore to your server").
11. Footer.

Additional pages:
- `/commands` - searchable command list grouped by category.
- `/features` - full feature breakdown.
- `/premium` - premium perks detail.
- `/404`.

Responsive: mobile-first. Grids collapse 3→2→1. Nav → hamburger. Reduce hero glow on mobile.

## Content Style
- Voice: confident, warm, concise. "Everything your server will adore."
- CTA wording: "Add to Discord", "Get started free", "Explore commands", "Upgrade".
- Headings: benefit-first, short. Eyebrows in uppercase rose.
- Avoid hype superlatives; show concrete numbers and features.

## adore.rest
- Broader feature set surfaced clearly (AI: Ask + Grok; economy + games; OCR; transcription; translation) - engagement only.
- More polished, lively visual design (glow, gradients, motion)
- Better commands discoverability (searchable explorer, copy buttons).
- Clear free-vs-premium value, transparent FAQ.
- Fast static site (Astro + Tailwind v4), accessible, great Lighthouse scores.

## Agent Build Instructions
- Stack: Astro 6 (static output) + Tailwind CSS v4 (`@tailwindcss/vite`, `@import "tailwindcss"`, `@theme`).
- Define tokens above in global CSS `@theme`. Dark mode is the default and only theme.
- Use semantic HTML, single h1 per page, visible focus states, `prefers-reduced-motion` guards.
- Components as `.astro` files; keep JS minimal (mobile menu, copy button, FAQ accordion, count-up).
- Use brand assets from `adore-asset/media/` copied into `public/`.
- Deploy target: Cloudflare Pages (build `npm run build`, output `dist`).
