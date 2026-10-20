# Dr. Denise Turley: personal website and brand kit

Technology should expand what's possible for people.

## What's here

| Path | What it is |
|---|---|
| `src/` | The website (Gatsby 5). |
| `src/data/site.js` | All site copy, links, bios, talks, and media entries. Edit this file to change content. |
| `brand/BRAND_GUIDE.md` | Positioning, architecture, voice, visual identity, keynote concept, open items. |
| `brand/LINKEDIN_KIT.md` | Paste-ready LinkedIn headline, About, Featured, settings, content rhythm, first-month prompts. |
| `brand/linkedin-banner.png` | LinkedIn banner, 1584 × 396 (SVG source alongside). |
| `_template-archive/` | The original e-commerce template, kept for reference. Not built. Safe to delete. |

## Pages

Home, About, Ideas, Speaking, Media (media kit with bios), Connect, 404.

## Before launch

Search `TODO` in `src/data/site.js` and work through the open items list in `brand/BRAND_GUIDE.md`. The essentials: headshot, LinkedIn URL, domain.

## Adding content

Add writing and video to the `writing` array in `src/data/site.js`:

```js
{ title: 'What I mean by more possible', pillar: 'opportunity', date: 'Nov 2026', url: 'https://...', type: 'Article' }
```

`pillar` is one of `possibility`, `opportunity`, `leadership`. Entries show on the home page and under the matching thread on the Ideas page.

## Run it

```bash
npm install
npm run develop   # http://localhost:8000
npm run build     # production build in /public
```

Deploys to Netlify as-is (`netlify.toml`). The speaking and contact forms use Netlify Forms, so submissions show up in the Netlify dashboard with no extra setup.
