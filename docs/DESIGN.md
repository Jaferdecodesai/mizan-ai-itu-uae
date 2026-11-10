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
