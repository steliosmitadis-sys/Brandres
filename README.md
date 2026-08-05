# Brand Restart — Landing Page

Production-ready conversion-focused landing page for the Brand Restart identity redesign service.

## Stack

- React 19 + TypeScript
- Vite 8
- Tailwind CSS v4
- Inter typeface

## Getting started

```bash
npm install
npm run dev
```

Open the local URL shown in the terminal (usually `http://localhost:5173`).

## Production build

```bash
npm run build
npm run preview
```

## Customisation

All content lives in `src/data/content.ts`. Update:

- Project case studies (titles, summaries, status labels)
- Price and delivery time
- Contact links (email, Instagram, Useme)
- FAQ answers

### Images & video

- Replace the before/after placeholders in `src/components/Work.tsx` with real image paths.
- Replace the founder portrait placeholder in `src/components/Founder.tsx`.
- In `src/components/Hero.tsx`, swap the gradient poster for a real poster image and add a `<video>` or embed once you have the sales-video URL.

### Form endpoint

In `src/components/Apply.tsx`, replace the `FORM_ENDPOINT` constant with your Formspree, Basin, or custom API URL.

## Design notes

- Colour system uses a controlled fire-orange accent on a warm off-white ground.
- Typography is restrained and hierarchical (Inter).
- No card grids, no glassmorphism, no fake social proof.
- Sticky navigation appears after scroll.
- Full keyboard and reduced-motion support.
