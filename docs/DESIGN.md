# DESIGN – Mizan war-room replay (v2, AqionLabs Design Kit v1)

Redesigned 2026-11-10 (Dubai, UTC+4) with the AqionLabs Design Kit (`/workspace/aqionlabs-design-kit/`, files copied to `web/assets/kit/`).

## Choice (kit §7 "How to pick")
Challenge type: government / public-service policy AI for the UAE → the kit maps **Gov, civic or smart-city (UAE)** to:
- **Palette: Cobalt Civic** (`data-palette="cobalt-civic"`): accent #4D8DFF on #0A0F1A / #131B2C. "Trustworthy, institutional, but alive" – right for a regulator-facing tool. Contrast (kit table): text/base-1 16.73:1, muted/base-1 7.26:1, accent/base-1 5.99:1, ink-on-accent 5.99:1 (AA). Button labels on the accent use `--c-on-accent` (#0A0F1A), never white (white on cobalt is only 3.20:1).
- **Type: Gulf Geometric** (`data-type="gulf"`): Unbounded (display) + Readex Pro (body, has Arabic for a future bilingual UI) + Space Mono (data, IDs, hashes, counters). Self-hosted from Google Fonts (SIL OFL 1.1, latin subset, `font-display: swap`) so the page has no third-party requests and passes the Worker's CSP.
- **3 signature elements (the kit's recommendation for this type):**
  1. **Split-flap counter (#09)** – the hero "run board": audit records, messages, gaps, KB docs, chunks. It flips when you switch Baseline ↔ Judge twist (44→51 records, 19→22 messages, 5→6 gaps), so the twist is visible at a glance.
  2. **Glass card with a single accent edge (#05)** – the dossier panel (selected event/message, claims, citation chips, trace).
  3. **Blueprint backdrop (#13)** – behind the hero only.

## Rules applied
- One accent: the primary CTA (Verify audit chain), the playhead/selection, links on hover, one hero phrase ("only a human can decide"), the dossier edge. Gap IDs, node counts and global-source chips were moved off the accent.
- Message types keep a categorical colour set (INFORM slate, REQUEST teal, ASSESS lavender, PROPOSE brass, OBJECT red, DECIDE white) – that is data encoding, not decoration. Verifier statuses: green / amber / red.
- Soft radius family only (6 / 12 / 20 / pill). No hard shadows.
- Mobile first (375 → 768 → 1280), kit spacing scale, 44px tap targets for buttons, chips, selects and seg toggle (citation chips grow to 44px on coarse pointers).
- Motion: only transform/opacity; split-flap flips use the kit's timing; reduced-motion block kept (tokens.css + elements.css).
- Not copied: no Cigna branding; Mizan keeps its own scale mark, recoloured to the palette.

## Screens
Before (live v1): `evidence/screens/before/`. After: `evidence/screens/after/`. Comparison: `evidence/screens/redesign_compare.png`.

## v3 – light base with matched dark components (2026-11-11, Dubai UTC+4)
Owner direction: "keep the background light but include the box colors and dark components at some sections in a matching manner".
- The kit ships dark palettes only, so a light surface set was **derived from Cobalt Civic** (`html[data-theme="light"]` in `app.css`): page #F3F6FB, cards #FFFFFF, cobalt-tinted box #E8F0FF, text #0A0F1A, muted #4B5872, border #D8E0EE. Accent stays #4D8DFF; where the accent is used as *text* on light it is #1F5FD6 (5.29:1 on the page). Button labels on the accent stay #0A0F1A (5.99:1), never white.
- Box colours: white cards with a soft shadow for the timeline, dossier, gaps, manifest and KB results; cobalt-tinted boxes for the fact pills, the gap register's UAE/global mapping blocks and the method columns.
- Dark components (the exact kit Cobalt Civic tokens via `.dark`): (1) the hero **run board** with split-flap counters, (2) a new **audit-chain panel** in the war-room (file, record count, head SHA-256, "Verify in this browser"), (3) the full-bleed **Y.3172 pipeline + readiness band**, (4) the **KB retrieval-eval** box. They alternate with light sections from top to bottom.
- Status colours have light and dark variants (light: ok #0A6E4C, weak #8A5300, bad #C0322B; global-source ink #5B47D6).
- Automated contrast scan over every visible text node (1440 and 375): 566 / 498 nodes checked, **0 below 4.5:1** (3:1 for large text).
- Screens: `evidence/screens/light/`; comparison `evidence/screens/light_compare.png` (dark v2 vs light v3).
