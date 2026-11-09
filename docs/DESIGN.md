# DESIGN – Mizan war-room replay

- Concept: a policy war-room, not a dashboard. Bone/ink palette, indigo accent, brass for proposals, red only for OBJECT/UNCITED. Inter + JetBrains Mono, self-hosted.
- Layout: hero with honesty labels → swimlane timeline (one lane per role + human; events on the upper sub-row, messages on the lower) with scrubber and speed → dossier panel for the selected item (claims, citation chips, verifier status, Y.3172 node, readiness dims, audit seq/hash, reasoning trace) → gap register → Y.3172 pipeline map → KB search (BM25 in browser) and eval box.
- Twist toggle: Baseline run vs Judge twist run (two real audit logs).
- Verify button: recomputes the SHA-256 chain client-side (Web Crypto) – identical to Python (parity test).
- Not copied: Cigna materials were used only as a polish bar; no Cigna branding, colours or assets. AqionLabs brand reference kept light: the product carries its own Mizan mark.
- Screens (live GitHub Pages, 2026-11-09 ~20:05 Dubai): `evidence/screens/{1440,768,375}-{top,selected,full}.png`. No console errors at any width; chain verify ✓ 51 records.
- Fixes after review: tablet header subtitle hidden <1100px; emphasis rendered in gap text; relative asset paths.
